import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import {
  AlertCircle,
  ArrowDownToLine,
  Check,
  LoaderCircle,
  X,
} from "lucide-react";
import type { JobStatus, ReviewStatus, Vehicle } from "./types";

export const statusLabels: Record<JobStatus | ReviewStatus, string> = {
  queued: "Đang chờ",
  running: "Đang phân tích",
  finalizing: "Đang lưu bằng chứng",
  stopping: "Đang dừng",
  completed: "Hoàn tất",
  cancelled: "Đã hủy",
  failed: "Có lỗi",
  interrupted: "Bị gián đoạn",
  pending: "Chờ duyệt",
  confirmed: "Đã xác nhận",
  dismissed: "Đã bỏ qua",
  resolved: "Đã xử lý",
};
export const vehicleLabels: Record<Vehicle, string> = {
  car: "Ô tô",
  motorcycle: "Xe máy",
  bus: "Xe buýt",
  truck: "Xe tải",
};
export const active = (status: JobStatus) =>
  ["queued", "running", "finalizing", "stopping"].includes(status);
export const number = (value: number) =>
  new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 1 }).format(value);
export const bytes = (value: number) =>
  value >= 1024 ** 3
    ? `${number(value / 1024 ** 3)} GB`
    : `${number(value / 1024 ** 2)} MB`;
export const duration = (value: number) =>
  value >= 3600
    ? `${Math.floor(value / 3600)} giờ ${Math.floor((value % 3600) / 60)} phút`
    : value >= 60
      ? `${Math.floor(value / 60)} phút ${Math.floor(value % 60)} giây`
      : `${number(value)} giây`;
export const stamp = (value: string | null | undefined) =>
  value
    ? new Date(value).toLocaleString("vi-VN", {
        hour: "2-digit",
        minute: "2-digit",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      })
    : "—";
export const clockTime = (value: number) =>
  `${Math.floor(value / 60)
    .toString()
    .padStart(2, "0")}:${Math.floor(value % 60)
    .toString()
    .padStart(2, "0")}`;
export const go = (path: string) => {
  if (
    window.dispatchEvent(
      new CustomEvent("curb:navigate", { detail: path, cancelable: true }),
    )
  )
    window.location.hash = path;
};

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      ...(options.body && !(options.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({
        detail: "Không kết nối được dịch vụ. Kiểm tra ứng dụng rồi thử lại.",
      }));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : "Dữ liệu không hợp lệ. Kiểm tra các trường rồi thử lại.",
    );
  }
  return response.json() as Promise<T>;
}

export const send = <T,>(path: string, body?: unknown, method = "POST") =>
  api<T>(path, {
    method,
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });

export function useResource<T>(path: string, interval = 0) {
  const [data, setData] = useState<T>();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [revision, setRevision] = useState(0);
  const refresh = useCallback(() => setRevision((n) => n + 1), []);
  useEffect(() => {
    let alive = true;
    let fetching = false;
    setLoading(true);
    const load = async () => {
      if (fetching) return;
      fetching = true;
      try {
        const result = await api<T>(path);
        if (alive) {
          setData(result);
          setError("");
        }
      } catch (e) {
        if (alive) setError((e as Error).message);
      } finally {
        fetching = false;
        if (alive) setLoading(false);
      }
    };
    void load();
    const timer = interval ? window.setInterval(load, interval) : undefined;
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [path, interval, revision]);
  return { data, error, loading, refresh };
}

type Notice = (message: string, error?: boolean) => void;
export const NoticeContext = createContext<Notice>(() => undefined);
export const useNotice = () => useContext(NoticeContext);
export const ConfirmContext = createContext<
  (title: string, message: string, action?: string) => Promise<boolean>
>(async () => false);
export const useConfirm = () => useContext(ConfirmContext);

export function Button({
  children,
  busy,
  variant = "default",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  busy?: boolean;
  variant?: "default" | "primary" | "danger" | "quiet";
}) {
  return (
    <button
      type="button"
      {...props}
      disabled={props.disabled || busy}
      className={`button ${variant} ${className}`}
    >
      {busy && <LoaderCircle size={16} className="spin" />}
      {children}
    </button>
  );
}

export function Badge({ status }: { status: JobStatus | ReviewStatus }) {
  return (
    <span className={`badge ${status}`}>
      <span className="status-dot" />
      {statusLabels[status]}
    </span>
  );
}

export function ErrorBox({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  if (!message) return null;
  return (
    <div className="error-box" role="alert">
      <AlertCircle size={19} />
      <span>{message}</span>
      {retry && <Button onClick={retry}>Thử lại</Button>}
    </div>
  );
}

export function Loading() {
  return (
    <div className="loading" role="status">
      <LoaderCircle className="spin" size={22} />
      Đang tải dữ liệu…
    </div>
  );
}

export function Empty({
  icon,
  title,
  children,
  action,
}: {
  icon: ReactNode;
  title: string;
  children?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <div className="empty-icon">{icon}</div>
      <h3>{title}</h3>
      {children && <p>{children}</p>}
      {action && <div className="actions">{action}</div>}
    </div>
  );
}

export function Modal({
  title,
  open,
  onClose,
  children,
  wide = false,
}: {
  title: string;
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (open && !ref.current?.open) ref.current?.showModal();
    else if (!open) ref.current?.close();
  }, [open]);
  return (
    <dialog
      ref={ref}
      className={wide ? "modal wide" : "modal"}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      aria-labelledby={`dialog-${title.replace(/\s/g, "-")}`}
    >
      <div className="modal-content">
        <div className="modal-heading">
          <h2 id={`dialog-${title.replace(/\s/g, "-")}`}>{title}</h2>
          <button
            className="icon-button"
            onClick={onClose}
            aria-label="Đóng cửa sổ"
          >
            <X size={21} />
          </button>
        </div>
        {open && children}
      </div>
    </dialog>
  );
}

export function Download({
  path,
  name,
  children,
  variant = "default",
}: {
  path: string;
  name: string;
  children?: ReactNode;
  variant?: "default" | "quiet";
}) {
  const [busy, setBusy] = useState(false);
  const notice = useNotice();
  const download = async () => {
    setBusy(true);
    try {
      const response = await fetch(`/api${path}`);
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail);
      }
      const url = URL.createObjectURL(await response.blob());
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = name;
      anchor.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 60000);
      notice("Đã chuẩn bị tệp tải xuống.");
    } catch (e) {
      notice((e as Error).message, true);
    } finally {
      setBusy(false);
    }
  };
  return (
    <Button busy={busy} variant={variant} onClick={download}>
      {!busy && <ArrowDownToLine size={16} />}
      {children ?? "Xuất dữ liệu"}
    </Button>
  );
}

export function Feedback({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<{ message: string; error: boolean }>();
  const timer = useRef<number | undefined>(undefined);
  const [confirm, setConfirm] = useState<{
    title: string;
    message: string;
    action: string;
    resolve: (value: boolean) => void;
  }>();
  const notice = useCallback<Notice>((message, error = false) => {
    window.clearTimeout(timer.current);
    setToast({ message, error });
    timer.current = window.setTimeout(
      () => setToast(undefined),
      error ? 10000 : 4500,
    );
  }, []);
  const ask = useCallback(
    (title: string, message: string, action = "Xác nhận") =>
      new Promise<boolean>((resolve) =>
        setConfirm({ title, message, action, resolve }),
      ),
    [],
  );
  const answer = (value: boolean) => {
    confirm?.resolve(value);
    setConfirm(undefined);
  };
  return (
    <NoticeContext.Provider value={notice}>
      <ConfirmContext.Provider value={ask}>
        {children}
        {toast && (
          <div
            className={`toast ${toast.error ? "toast-error" : ""}`}
            role={toast.error ? "alert" : "status"}
          >
            {toast.error ? <AlertCircle size={19} /> : <Check size={19} />}
            <span>{toast.message}</span>
            <button
              className="icon-button"
              onClick={() => setToast(undefined)}
              aria-label="Đóng thông báo"
            >
              <X size={17} />
            </button>
          </div>
        )}
        <Modal
          open={!!confirm}
          title={confirm?.title ?? "Xác nhận"}
          onClose={() => answer(false)}
        >
          <p className="muted">{confirm?.message}</p>
          <div className="modal-actions">
            <Button onClick={() => answer(false)}>Quay lại</Button>
            <Button variant="danger" onClick={() => answer(true)}>
              {confirm?.action}
            </Button>
          </div>
        </Modal>
      </ConfirmContext.Provider>
    </NoticeContext.Provider>
  );
}
