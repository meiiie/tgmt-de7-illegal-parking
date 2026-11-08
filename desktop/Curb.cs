using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

[assembly: System.Reflection.AssemblyProduct("Curb")]
[assembly: System.Reflection.AssemblyDescription("Giám sát dừng đỗ đường phố")]

static class Program
{
    [DllImport("user32.dll")] static extern bool SetProcessDPIAware();
    [DllImport("shell32.dll", CharSet = CharSet.Unicode)] static extern int SetCurrentProcessExplicitAppUserModelID(string id);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern IntPtr FindWindow(string cls, string title);
    [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr window);
    [DllImport("user32.dll")] static extern bool ShowWindow(IntPtr window, int command);
    public const string Title = "Curb · Giám sát dừng đỗ";
    public static string RestartData;
    public static bool SaveDataChoice;
    public static readonly string DataChoiceFile = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Curb", "desktop-data-path.txt");

    [STAThread]
    static void Main(string[] args)
    {
        SetProcessDPIAware();
        SetCurrentProcessExplicitAppUserModelID("Curb.Desktop");
        var data = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Curb", "data");
        SaveDataChoice = args.Length == 0;
        if (args.Length == 2 && args[0] == "--data-dir") data = Path.GetFullPath(args[1]);
        else if (File.Exists(DataChoiceFile)) {
            data = File.ReadAllText(DataChoiceFile, Encoding.UTF8).Trim();
            if (!Path.IsPathRooted(data) || !Directory.Exists(data)) {
                MessageBox.Show("Thư mục dữ liệu đã chọn không còn truy cập được. Kết nối lại ổ lưu trữ rồi mở Curb.\n" + data, "Curb", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }
        }
        bool first;
        using (var mutex = new Mutex(true, "Local\\Curb.Desktop", out first))
        {
            if (!first)
            {
                var window = FindWindow(null, Title);
                if (window != IntPtr.Zero) { ShowWindow(window, 9); SetForegroundWindow(window); }
                return;
            }
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            try { Application.Run(new CurbWindow(data)); }
            catch (Exception e) { MessageBox.Show(e.Message, "Không thể mở Curb", MessageBoxButtons.OK, MessageBoxIcon.Error); }
        }
        if (RestartData != null) Process.Start(new ProcessStartInfo(Application.ExecutablePath, SaveDataChoice ? "" : "--data-dir \"" + RestartData + "\"") { UseShellExecute = false });
    }
}

sealed class CurbWindow : Form
{
    readonly string root = AppDomain.CurrentDomain.BaseDirectory;
    readonly string data;
    readonly WebView2 view = new WebView2();
    readonly Label status = new Label();
    readonly System.Windows.Forms.Timer monitor = new System.Windows.Forms.Timer();
    Process backend;
    ProcessTree tree;
    StreamWriter log;
    bool closing;
    bool restoring;
    string origin;

    public CurbWindow(string dataPath)
    {
        data = dataPath;
        Text = Program.Title;
        StartPosition = FormStartPosition.CenterScreen;
        ClientSize = new Size(1360, 880);
        MinimumSize = new Size(1024, 700);
        BackColor = Color.FromArgb(243, 243, 240);
        Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
        status.Dock = DockStyle.Fill;
        status.TextAlign = ContentAlignment.MiddleCenter;
        status.Font = new Font("Segoe UI", 16);
        status.Text = "Curb " + BuildInfo.Version + "\nĐang mở trạm giám sát…";
        status.Paint += delegate(object sender, PaintEventArgs e) {
            e.Graphics.DrawIcon(Icon, new Rectangle(status.Width / 2 - 32, status.Height / 2 - 115, 64, 64));
        };
        view.Dock = DockStyle.Fill;
        Controls.Add(view);
        Controls.Add(status);
        Shown += async delegate { await StartService(); };
        FormClosing += OnClosing;
        monitor.Interval = 1500;
        monitor.Tick += delegate {
            if (!closing && backend != null && backend.HasExited)
            {
                monitor.Stop();
                MessageBox.Show(this, "Dịch vụ đã dừng ngoài dự kiến. Đóng và mở lại Curb.\nNhật ký: " + Path.Combine(data, "desktop.log"), "Curb", MessageBoxButtons.OK, MessageBoxIcon.Error);
                Close();
            }
        };
    }

    async Task StartService()
    {
        try
        {
            Directory.CreateDirectory(data);
            log = new StreamWriter(Path.Combine(data, "desktop.log"), true, Encoding.UTF8) { AutoFlush = true };
            log.WriteLine("\nDesktop start " + DateTimeOffset.Now.ToString("O"));
            CoreWebView2Environment.GetAvailableBrowserVersionString();
            var info = new ProcessStartInfo(Path.Combine(root, "runtime", "python.exe"), "-X utf8 -m curb.desktop_service --data-dir \"" + data + "\"") {
                WorkingDirectory = root, UseShellExecute = false, CreateNoWindow = true,
                RedirectStandardInput = true, RedirectStandardOutput = true, RedirectStandardError = true,
                StandardOutputEncoding = Encoding.UTF8, StandardErrorEncoding = Encoding.UTF8
            };
            info.EnvironmentVariables["PATH"] = Path.Combine(root, "bin") + ";" + Environment.GetEnvironmentVariable("PATH");
            info.EnvironmentVariables["PYTHONUTF8"] = "1";
            info.EnvironmentVariables["PYTHONDONTWRITEBYTECODE"] = "1";
            info.EnvironmentVariables["YOLO_CONFIG_DIR"] = Path.Combine(data, "ultralytics");
            info.EnvironmentVariables["MPLCONFIGDIR"] = Path.Combine(data, "matplotlib");
            info.EnvironmentVariables["CURB_EDITION"] = "Desktop · CPU";
            var ready = new TaskCompletionSource<string>();
            tree = new ProcessTree();
            backend = new Process { StartInfo = info, EnableRaisingEvents = true };
            backend.OutputDataReceived += delegate(object sender, DataReceivedEventArgs e) {
                if (e.Data != null && e.Data.StartsWith("CURB_READY ")) ready.TrySetResult(e.Data.Substring(11));
                else WriteLog(e.Data);
            };
            backend.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) { WriteLog(e.Data); };
            backend.Exited += delegate { ready.TrySetException(new Exception("Không khởi động được dịch vụ. Xem desktop.log trong thư mục dữ liệu.")); };
            backend.Start();
            tree.Add(backend);
            backend.BeginOutputReadLine();
            backend.BeginErrorReadLine();
            if (await Task.WhenAny(ready.Task, Task.Delay(45000)) != ready.Task) throw new TimeoutException("Dịch vụ khởi động quá 45 giây.");
            origin = await ready.Task;
            if (closing) return;
            await Task.Run(async delegate {
                for (int i = 0; i < 90; i++)
                {
                    if (backend.HasExited) throw new Exception("Dịch vụ đã dừng khi khởi động.");
                    try {
                        var request = (HttpWebRequest)WebRequest.Create(origin + "/api/settings");
                        request.Proxy = null; request.Timeout = 1000;
                        using (var response = request.GetResponse()) { return; }
                    } catch (WebException) { }
                    await Task.Delay(250);
                }
                throw new TimeoutException("Dịch vụ không phản hồi.");
            });
            if (closing) return;
            var environment = await CoreWebView2Environment.CreateAsync(null, Path.Combine(data, "webview"));
            status.Text = "Curb " + BuildInfo.Version + "\nĐang tải không gian làm việc…";
            await view.EnsureCoreWebView2Async(environment);
            if (closing) return;
            view.CoreWebView2.Settings.AreDevToolsEnabled = false;
            view.CoreWebView2.Settings.IsPasswordAutosaveEnabled = false;
            view.CoreWebView2.Settings.IsGeneralAutofillEnabled = false;
            view.CoreWebView2.Settings.AreDefaultContextMenusEnabled = false;
            view.CoreWebView2.NavigationStarting += delegate(object sender, CoreWebView2NavigationStartingEventArgs e) {
                Uri uri;
                if (!Uri.TryCreate(e.Uri, UriKind.Absolute, out uri) || uri.GetLeftPart(UriPartial.Authority) != origin) e.Cancel = true;
            };
            view.CoreWebView2.NewWindowRequested += delegate(object sender, CoreWebView2NewWindowRequestedEventArgs e) {
                e.Handled = true;
                Uri uri;
                if (Uri.TryCreate(e.Uri, UriKind.Absolute, out uri) && uri.GetLeftPart(UriPartial.Authority) == origin) view.CoreWebView2.Navigate(e.Uri);
                else if (e.IsUserInitiated && uri != null && uri.Scheme == "https" && uri.UserInfo.Length == 0) {
                    try { Process.Start(new ProcessStartInfo(uri.AbsoluteUri) { UseShellExecute = true }); }
                    catch (Exception error) { MessageBox.Show(this, "Không mở được trình duyệt. " + error.Message, "Curb"); }
                }
            };
            view.CoreWebView2.WebMessageReceived += async delegate(object sender, CoreWebView2WebMessageReceivedEventArgs e) {
                Uri uri;
                if (!Uri.TryCreate(e.Source, UriKind.Absolute, out uri) || uri.GetLeftPart(UriPartial.Authority) != origin) return;
                string command;
                try { command = e.TryGetWebMessageAsString(); } catch (ArgumentException) { return; }
                if (command == "open-data") Process.Start(new ProcessStartInfo("explorer.exe", "\"" + data + "\"") { UseShellExecute = true });
                else if (command == "restore-backup") await RestoreBackup();
            };
            view.CoreWebView2.PermissionRequested += delegate(object sender, CoreWebView2PermissionRequestedEventArgs e) { e.State = CoreWebView2PermissionState.Deny; };
            view.CoreWebView2.DownloadStarting += delegate(object sender, CoreWebView2DownloadStartingEventArgs e) {
                e.Handled = true;
                var deferral = e.GetDeferral();
                BeginInvoke(new Action(delegate {
                    try {
                        using (var dialog = new SaveFileDialog { FileName = Path.GetFileName(e.ResultFilePath), OverwritePrompt = true }) {
                            if (!closing && dialog.ShowDialog(this) == DialogResult.OK) e.ResultFilePath = dialog.FileName;
                            else e.Cancel = true;
                        }
                    } finally { deferral.Complete(); }
                }));
            };
            view.CoreWebView2.NavigationCompleted += delegate { status.Visible = false; };
            view.CoreWebView2.Navigate(origin + "/");
            monitor.Start();
        }
        catch (Exception e)
        {
            WriteLog(e.ToString());
            if (!closing) {
                MessageBox.Show(this, "Không mở được Curb.\n" + e.Message + "\n\nNhật ký: " + Path.Combine(data, "desktop.log") + "\nNếu thiếu WebView2, chạy lại bộ cài khi có Internet.", "Curb", MessageBoxButtons.OK, MessageBoxIcon.Error);
                Close();
            }
        }
    }

    void WriteLog(string line) { if (line != null && log != null) lock (log) { log.WriteLine(line); } }

    async Task RestoreBackup()
    {
        if (restoring || closing) return;
        string archive;
        using (var picker = new OpenFileDialog { Title = "Chọn bản sao lưu Curb", Filter = "Bản sao lưu Curb (*.zip)|*.zip", CheckFileExists = true }) {
            if (picker.ShowDialog(this) != DialogResult.OK) return;
            archive = picker.FileName;
        }
        if (MessageBox.Show(this, "Curb sẽ khôi phục vào thư mục mới và mở lại ứng dụng. Lượt xử lý đang chạy sẽ dừng. Dữ liệu hiện tại được giữ nguyên.\n\nTiếp tục khôi phục?", "Khôi phục bản sao lưu", MessageBoxButtons.OKCancel, MessageBoxIcon.Question) != DialogResult.OK) return;
        restoring = true;
        var destination = Path.Combine(Path.GetDirectoryName(data), "restored-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + "-" + Guid.NewGuid().ToString("N").Substring(0, 6));
        status.Text = "Đang khôi phục bản sao lưu…\nDữ liệu hiện tại vẫn được giữ nguyên.";
        status.Visible = true;
        status.BringToFront();
        try {
            var error = await Task.Run(delegate {
                var info = new ProcessStartInfo(Path.Combine(root, "runtime", "python.exe"), "-X utf8 -m curb.backup \"" + archive + "\" --destination \"" + destination + "\"") {
                    WorkingDirectory = root, UseShellExecute = false, CreateNoWindow = true, RedirectStandardError = true, RedirectStandardOutput = true,
                    StandardErrorEncoding = Encoding.UTF8, StandardOutputEncoding = Encoding.UTF8
                };
                using (var process = Process.Start(info)) {
                    var errors = process.StandardError.ReadToEnd();
                    process.WaitForExit();
                    return process.ExitCode == 0 ? null : errors;
                }
            });
            if (error != null) throw new Exception(error);
            if (Program.SaveDataChoice) {
                Directory.CreateDirectory(Path.GetDirectoryName(Program.DataChoiceFile));
                var temp = Program.DataChoiceFile + ".tmp";
                File.WriteAllText(temp, destination, Encoding.UTF8);
                if (File.Exists(Program.DataChoiceFile)) File.Replace(temp, Program.DataChoiceFile, null);
                else File.Move(temp, Program.DataChoiceFile);
            }
            Program.RestartData = destination;
            restoring = false;
            Close();
        } catch (Exception error) {
            WriteLog(error.ToString());
            MessageBox.Show(this, "Không khôi phục được bản sao lưu. Dữ liệu hiện tại không thay đổi.\n" + error.Message, "Curb", MessageBoxButtons.OK, MessageBoxIcon.Error);
            status.Visible = false;
            restoring = false;
        }
    }

    async void OnClosing(object sender, FormClosingEventArgs e)
    {
        if (restoring) { e.Cancel = true; return; }
        if (closing) return;
        e.Cancel = true;
        closing = true;
        monitor.Stop();
        status.Text = "Đang lưu trạng thái và dừng xử lý…";
        status.Visible = true;
        status.BringToFront();
        view.Dispose();
        await Task.Run(delegate {
            if (backend != null) {
                try {
                    if (!backend.HasExited) { backend.StandardInput.WriteLine("STOP"); backend.StandardInput.Flush(); backend.WaitForExit(25000); }
                } catch (InvalidOperationException) { } catch (IOException) { }
            }
            if (tree != null) tree.Dispose();
        });
        Close();
    }
}

sealed class ProcessTree : IDisposable
{
    [StructLayout(LayoutKind.Sequential)] struct BasicLimits {
        public long PerProcessUserTimeLimit, PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize, MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass, SchedulingClass;
    }
    [StructLayout(LayoutKind.Sequential)] struct IoCounters { public ulong ReadOperationCount, WriteOperationCount, OtherOperationCount, ReadTransferCount, WriteTransferCount, OtherTransferCount; }
    [StructLayout(LayoutKind.Sequential)] struct ExtendedLimits {
        public BasicLimits BasicLimitInformation;
        public IoCounters IoInfo;
        public UIntPtr ProcessMemoryLimit, JobMemoryLimit, PeakProcessMemoryUsed, PeakJobMemoryUsed;
    }
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)] static extern IntPtr CreateJobObject(IntPtr attributes, string name);
    [DllImport("kernel32.dll")] static extern bool SetInformationJobObject(IntPtr job, int cls, ref ExtendedLimits limits, uint size);
    [DllImport("kernel32.dll")] static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    IntPtr handle;
    public ProcessTree() {
        handle = CreateJobObject(IntPtr.Zero, null);
        var limits = new ExtendedLimits(); limits.BasicLimitInformation.LimitFlags = 0x2000;
        if (handle == IntPtr.Zero || !SetInformationJobObject(handle, 9, ref limits, (uint)Marshal.SizeOf(limits))) throw new Exception("Không quản lý được tiến trình xử lý.");
    }
    public void Add(Process process) { if (!AssignProcessToJobObject(handle, process.Handle)) { process.Kill(); throw new Exception("Không gắn được dịch vụ vào phiên desktop."); } }
    public void Dispose() { if (handle != IntPtr.Zero) { CloseHandle(handle); handle = IntPtr.Zero; } }
}
