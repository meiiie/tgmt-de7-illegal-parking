using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using System.Windows.Forms;

[assembly: AssemblyProduct("Curb Quick Install")]
[assembly: AssemblyDescription("Curb · Giám sát dừng đỗ đường phố")]

static class SetupLauncher
{
    [STAThread]
    static int Main(string[] args)
    {
        Application.EnableVisualStyles();
        var directory = Path.Combine(Path.GetTempPath(), "Curb-Setup-" + Guid.NewGuid().ToString("N"));
        var installer = Path.Combine(directory, "Curb-Package.exe");
        try {
            Directory.CreateDirectory(directory);
            using (var resource = Assembly.GetExecutingAssembly().GetManifestResourceStream("Curb.Payload.exe"))
            using (var output = new FileStream(installer, FileMode.CreateNew, FileAccess.Write, FileShare.None)) {
                if (resource == null) throw new IOException("Bộ cài thiếu thành phần. Hãy tải lại từ trang phát hành chính thức.");
                resource.CopyTo(output);
            }
            var arguments = new StringBuilder("/SILENT /SP- /NORESTART");
            foreach (var argument in args) arguments.Append(" ").Append(Quote(argument));
            using (var process = Process.Start(new ProcessStartInfo(installer, arguments.ToString()) {
                UseShellExecute = false, CreateNoWindow = true, WorkingDirectory = directory
            })) {
                process.WaitForExit();
                return process.ExitCode;
            }
        } catch (Exception error) {
            MessageBox.Show("Không cài được Curb.\n" + error.Message + "\n\nTải lại tại github.com/meiiie/tgmt-de7-illegal-parking/releases", "Curb " + BuildInfo.Version, MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        } finally {
            try { File.Delete(installer); Directory.Delete(directory); }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
        }
    }

    static string Quote(string value)
    {
        var result = new StringBuilder("\"");
        var slashes = 0;
        foreach (var character in value) {
            if (character == '\\') { slashes++; continue; }
            if (character == '"') {
                result.Append('\\', slashes * 2 + 1).Append('"');
            } else {
                result.Append('\\', slashes).Append(character);
            }
            slashes = 0;
        }
        return result.Append('\\', slashes * 2).Append('"').ToString();
    }
}
