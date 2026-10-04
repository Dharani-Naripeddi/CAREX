import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { notificationsApi } from "../../services/api";
import { AppNotification, UnreadCountResponse } from "../../types/support_services";
import { Badge } from "../ui/Badge";
import {
  Bell,
  CheckCircle,
  AlertTriangle,
  Info,
  ShieldCheck,
  Clock,
  ExternalLink,
} from "lucide-react";

interface NotificationDropdownProps {
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
}

export const NotificationDropdown: React.FC<NotificationDropdownProps> = ({
  isOpen,
  onToggle,
  onClose,
}) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: unreadData } = useQuery<UnreadCountResponse>({
    queryKey: ["unreadNotificationsCount"],
    queryFn: notificationsApi.getUnreadCount,
    refetchInterval: 10000,
  });

  const { data: notifications, isLoading } = useQuery<AppNotification[]>({
    queryKey: ["notificationsList"],
    queryFn: () => notificationsApi.list({ limit: 10 }),
    enabled: isOpen,
    refetchInterval: 10000,
  });

  const markReadMutation = useMutation({
    mutationFn: (id: number) => notificationsApi.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["unreadNotificationsCount"] });
      queryClient.invalidateQueries({ queryKey: ["notificationsList"] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => notificationsApi.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["unreadNotificationsCount"] });
      queryClient.invalidateQueries({ queryKey: ["notificationsList"] });
    },
  });

  const unreadCount = unreadData?.unread_count || 0;
  const criticalCount = unreadData?.critical_unread_count || 0;

  const handleNotificationClick = (notif: AppNotification) => {
    if (!notif.is_read) {
      markReadMutation.mutate(notif.id);
    }
    onClose();

    // Navigate to related entity page
    switch (notif.related_entity) {
      case "LAB_ORDER":
        navigate("/lab");
        break;
      case "PRESCRIPTION":
      case "INVENTORY":
        navigate("/pharmacy");
        break;
      case "INVOICE":
        navigate("/billing");
        break;
      case "EMERGENCY":
        navigate("/emergency");
        break;
      case "ADMISSION":
        navigate("/ipd");
        break;
      default:
        break;
    }
  };

  const getIcon = (type: string) => {
    switch (type) {
      case "CRITICAL":
      case "ALERT":
        return <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />;
      case "WARNING":
        return <Clock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />;
      case "SUCCESS":
        return <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />;
      default:
        return <Info className="w-4 h-4 text-sky-400 shrink-0 mt-0.5" />;
    }
  };

  return (
    <div className="relative">
      <button
        onClick={onToggle}
        className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 relative transition-colors"
        aria-label="Notifications"
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && (
          <span
            className={`absolute top-1.5 right-1.5 w-2.5 h-2.5 rounded-full ring-2 ring-slate-900 ${
              criticalCount > 0 ? "bg-rose-500 animate-ping" : "bg-sky-500 animate-pulse"
            }`}
          />
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl p-3 z-50 animate-in fade-in zoom-in-95">
          <div className="flex items-center justify-between pb-2.5 border-b border-slate-800 text-xs font-bold text-white">
            <div className="flex items-center gap-2">
              <span>Clinical & System Alerts</span>
              {unreadCount > 0 && (
                <Badge variant={criticalCount > 0 ? "critical" : "info"} size="sm">
                  {unreadCount} Unread
                </Badge>
              )}
            </div>

            {unreadCount > 0 && (
              <button
                onClick={() => markAllReadMutation.mutate()}
                className="text-[11px] text-sky-400 hover:text-sky-300 font-medium"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="py-2 space-y-2 max-h-80 overflow-y-auto pr-1">
            {isLoading ? (
              <div className="py-8 text-center text-xs text-slate-400">Loading notifications...</div>
            ) : !notifications || notifications.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500">No recent notifications</div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  onClick={() => handleNotificationClick(n)}
                  className={`p-2.5 rounded-xl border transition-all cursor-pointer flex items-start gap-2.5 ${
                    !n.is_read
                      ? n.type === "ALERT" || n.type === "CRITICAL"
                        ? "bg-rose-950/20 border-rose-500/30 text-rose-200 hover:bg-rose-950/30"
                        : "bg-sky-950/20 border-sky-500/30 text-sky-200 hover:bg-sky-950/30"
                      : "bg-slate-950/40 border-slate-800 text-slate-400 hover:bg-slate-800/40"
                  }`}
                >
                  {getIcon(n.type)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span className={`text-xs font-bold truncate ${!n.is_read ? "text-white" : "text-slate-300"}`}>
                        {n.title}
                      </span>
                      {!n.is_read && (
                        <span className="w-1.5 h-1.5 rounded-full bg-sky-400 shrink-0" />
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">{n.message}</p>
                    <div className="flex items-center justify-between pt-1 text-[10px] text-slate-500">
                      <span>{new Date(n.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                      {n.related_entity && (
                        <span className="flex items-center gap-0.5 font-mono text-sky-400 hover:underline">
                          View {n.related_entity} <ExternalLink className="w-2.5 h-2.5" />
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
