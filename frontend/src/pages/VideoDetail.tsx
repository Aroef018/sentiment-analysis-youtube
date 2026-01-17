import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import api from "../api/axios";
import { logoutApi } from "../api/auth.api";
import {
  Info,
  MessageCircle,
  ThumbsUp,
  ArrowLeft,
  Search,
  BarChart3,
} from "lucide-react";

type DetailResponse = {
  video: {
    id: string;
    title: string;
    channel: string;
    thumbnail_url?: string;
    like_count?: number;
    comment_count?: number;
    published_at?: string | null;
  };
  analysis: {
    id: string;
    created_at?: string | null;
    total_comments: number;
    positive: number;
    neutral: number;
    negative: number;
    percentages: {
      positive: number;
      neutral: number;
      negative: number;
    };
  };
};

type CommentItem = {
  id: string;
  author: string;
  text: string;
  sentiment: "positive" | "neutral" | "negative";
  like_count: number;
  published_at?: string | null;
  is_top_level: boolean;
};

type CommentsResponse = {
  items: CommentItem[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
  filter: string;
};

const VideoDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<DetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  // Comments state
  const [showComments, setShowComments] = useState<boolean>(false);
  const [comments, setComments] = useState<CommentsResponse | null>(null);
  const [commentsLoading, setCommentsLoading] = useState<boolean>(false);
  const [sentimentFilter, setSentimentFilter] = useState<string>("all");
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [commentsError, setCommentsError] = useState<string | null>(null);

  const navigate = useNavigate();
  const handleLogout = async () => {
    try {
      await logoutApi();
    } catch {
      // ignore client-side logout is enough
    }
    localStorage.removeItem("token");
    localStorage.removeItem("last_analysis_result");
    localStorage.removeItem("last_analysis_url");
    navigate("/login");
  };

  // Check authentication on mount
  useEffect(() => {
    const token =
      localStorage.getItem("accessToken") || localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }
  }, [navigate]);

  useEffect(() => {
    const fetchDetail = async () => {
      if (!id) return;
      setLoading(true);
      setError("");
      try {
        const res = await api.get(`/analysis/detail/${id}`);
        setData(res.data);
      } catch (err) {
        const error = err as { response?: { data?: { detail?: string } } };
        const msg = error?.response?.data?.detail || "Gagal memuat detail";
        setError(msg);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [id]);

  const fetchComments = async (page: number = 1, sentiment: string = "all") => {
    if (!id) return;
    setCommentsLoading(true);
    setCommentsError(null);
    try {
      const params: Record<string, number | string> = { page, limit: 20 };
      if (sentiment !== "all") {
        params.sentiment = sentiment;
      }
      console.log("Fetching comments with params:", params);
      const res = await api.get(`/analysis/comments/${id}`, { params });
      console.log("Comments response:", res.data);
      setComments(res.data);
      setCurrentPage(page);
      setSentimentFilter(sentiment);
    } catch (err) {
      const error = err as {
        response?: { data?: { detail?: string } };
        message?: string;
      };
      console.error("Gagal memuat komentar:", error);
      console.error("Error response:", error?.response?.data);
      console.error("Error message:", error?.message);
      setCommentsError(
        error?.response?.data?.detail ||
          error?.message ||
          "Gagal memuat komentar"
      );
    } finally {
      setCommentsLoading(false);
    }
  };

  const truncateText = (text: string, maxLength: number = 200) => {
    return text.length > maxLength
      ? text.substring(0, maxLength) + "..."
      : text;
  };

  const insightText = (d: DetailResponse | null) => {
    if (!d) return "";
    const p = d.analysis.percentages.positive;
    const n = d.analysis.percentages.neutral;
    const ng = d.analysis.percentages.negative;
    const total = d.analysis.total_comments;
    return `Hasil analisis: Positif ${p}%, Netral ${n}%, Negatif ${ng}% dari ${total} komentar.`;
  };

  return (
    <div className="min-h-screen bg-white flex flex-col md:flex-row">
      {/* Sidebar */}
      <div className="w-full md:w-64 bg-gray-50 border-b md:border-r border-gray-200 p-6">
        <h1 className="text-xl font-bold text-gray-900 mb-8">
          Analisis Sentimen
        </h1>
        <nav className="space-y-2">
          <a
            href="/"
            className="flex items-center gap-3 text-gray-600 hover:bg-gray-100 px-4 py-3 rounded-lg transition"
          >
            <Search size={18} /> Analisis
          </a>
          <a
            href="/history"
            className="flex items-center gap-3 text-gray-600 hover:bg-gray-100 px-4 py-3 rounded-lg transition"
          >
            <BarChart3 size={18} /> Riwayat
          </a>
          <button
            onClick={() => navigate(-1)}
            className="w-full text-left flex items-center gap-3 text-gray-600 hover:bg-gray-100 px-4 py-3 rounded-lg transition"
          >
            <ArrowLeft size={18} /> Kembali
          </button>
        </nav>
        <button
          onClick={handleLogout}
          className="hidden md:block w-full mt-8 text-red-600 hover:bg-red-50 px-4 py-3 rounded-lg font-medium transition"
        >
          Logout
        </button>
      </div>

      <div className="flex-1 p-4 md:p-10 overflow-y-auto bg-linear-to-br from-blue-50/30 via-white to-purple-50/20">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-1 md:mb-2">
            Detail Analisis Video
          </h2>
          <p className="text-gray-500 mb-4 md:mb-6 text-sm md:text-base">
            Lihat ringkasan lengkap dari analisis terakhir
          </p>

          {loading && (
            <div className="bg-white p-4 md:p-6 rounded-3xl border border-gray-100 text-center text-gray-500 text-sm md:text-base">
              Memuat detail...
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 p-3 md:p-4 rounded-2xl text-red-600 font-semibold mb-6 text-sm md:text-base">
              {error}
            </div>
          )}

          {data && (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 md:gap-8 animate-in fade-in duration-700">
                <div className="lg:col-span-2 space-y-4 md:space-y-6">
                  <div className="bg-white p-4 md:p-6 rounded-3xl border border-gray-100 shadow-sm flex flex-col gap-4">
                    <img
                      src={
                        data.video.thumbnail_url ||
                        "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&q=80&w=400"
                      }
                      className="w-full h-40 md:h-32 object-cover rounded-2xl"
                      alt="thumbnail"
                    />
                    <div className="flex-1">
                      <h3 className="text-lg md:text-xl font-bold text-gray-800 leading-tight mb-2">
                        {data.video.title}
                      </h3>
                      <p className="text-blue-600 font-medium mb-3 text-sm md:text-base">
                        {data.video.channel}
                      </p>
                      <div className="flex gap-3 md:gap-6 text-gray-500 text-xs md:text-sm">
                        <div className="flex items-center gap-2">
                          <ThumbsUp size={16} /> {data.video.like_count ?? "-"}
                        </div>
                        <div className="flex items-center gap-2">
                          <MessageCircle size={16} />{" "}
                          {data.video.comment_count ?? 0} Komentar
                        </div>
                      </div>
                      <p className="text-xs text-gray-400 mt-3">
                        Dianalisis pada:{" "}
                        {data.analysis.created_at
                          ? new Date(
                              data.analysis.created_at
                            ).toLocaleDateString("id-ID", {
                              day: "numeric",
                              month: "long",
                              year: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "-"}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 md:gap-4">
                    {[
                      {
                        label: "Positif",
                        val: data.analysis.positive,
                        color: "text-green-600",
                        bg: "bg-green-50",
                      },
                      {
                        label: "Netral",
                        val: data.analysis.neutral,
                        color: "text-yellow-600",
                        bg: "bg-yellow-50",
                      },
                      {
                        label: "Negatif",
                        val: data.analysis.negative,
                        color: "text-red-600",
                        bg: "bg-red-50",
                      },
                    ].map((stat, i) => (
                      <div
                        key={i}
                        className={`${stat.bg} p-3 md:p-4 rounded-2xl border border-white/50 text-center`}
                      >
                        <p
                          className={`text-xl md:text-2xl font-black ${stat.color}`}
                        >
                          {stat.val}
                        </p>
                        <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">
                          {stat.label}
                        </p>
                      </div>
                    ))}
                  </div>

                  <div className="bg-blue-600 p-4 md:p-6 rounded-3xl text-white">
                    <div className="flex items-center gap-2 mb-2 font-bold uppercase text-xs tracking-widest opacity-80">
                      <Info size={14} /> Kesimpulan
                    </div>
                    <p className="text-sm md:text-lg leading-relaxed">
                      {insightText(data)}
                    </p>
                  </div>
                </div>

                <div className="bg-white p-4 md:p-8 rounded-3xl border border-gray-100 shadow-sm">
                  <h4 className="font-bold text-gray-800 mb-4 text-sm md:text-base">
                    Persentase Sentimen
                  </h4>
                  <div className="space-y-2 text-xs md:text-sm text-gray-700">
                    <div className="flex justify-between">
                      <span>Positif</span>
                      <span className="font-bold">
                        {data.analysis.percentages.positive}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Netral</span>
                      <span className="font-bold">
                        {data.analysis.percentages.neutral}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Negatif</span>
                      <span className="font-bold">
                        {data.analysis.percentages.negative}%
                      </span>
                    </div>
                  </div>
                  <div className="mt-4 md:mt-6 text-center">
                    <p className="text-xs md:text-sm text-gray-400">
                      Total data diolah:
                    </p>
                    <p className="text-xl md:text-2xl font-bold text-gray-800">
                      {data.analysis.total_comments} Komentar
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-8 md:mt-10">
                <button
                  onClick={() => {
                    if (!showComments) {
                      fetchComments(1, "all");
                    }
                    setShowComments(!showComments);
                  }}
                  className="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 transition-all flex items-center justify-center gap-2"
                >
                  <MessageCircle size={20} />
                  {showComments ? "Tutup Komentar" : "Lihat Semua Komentar"}
                </button>

                {showComments && (
                  <div className="mt-6 bg-white p-4 md:p-6 rounded-lg border">
                    <div className="mb-4 flex flex-wrap gap-2">
                      <button
                        onClick={() => fetchComments(1, "all")}
                        className={
                          sentimentFilter === "all"
                            ? "bg-gray-800 text-white px-4 py-2 rounded font-semibold"
                            : "bg-gray-100 px-4 py-2 rounded hover:bg-gray-200"
                        }
                      >
                        Semua
                      </button>
                      <button
                        onClick={() => fetchComments(1, "positive")}
                        className={
                          sentimentFilter === "positive"
                            ? "bg-green-600 text-white px-4 py-2 rounded font-semibold"
                            : "bg-gray-100 px-4 py-2 rounded hover:bg-gray-200"
                        }
                      >
                        🟢 Positif
                      </button>
                      <button
                        onClick={() => fetchComments(1, "neutral")}
                        className={
                          sentimentFilter === "neutral"
                            ? "bg-yellow-600 text-white px-4 py-2 rounded font-semibold"
                            : "bg-gray-100 px-4 py-2 rounded hover:bg-gray-200"
                        }
                      >
                        🟡 Netral
                      </button>
                      <button
                        onClick={() => fetchComments(1, "negative")}
                        className={
                          sentimentFilter === "negative"
                            ? "bg-red-600 text-white px-4 py-2 rounded font-semibold"
                            : "bg-gray-100 px-4 py-2 rounded hover:bg-gray-200"
                        }
                      >
                        🔴 Negatif
                      </button>
                    </div>

                    {commentsLoading ? (
                      <div className="text-center text-gray-500 py-8">
                        Memuat komentar...
                      </div>
                    ) : commentsError ? (
                      <div className="text-center py-8">
                        <p className="text-red-600 font-semibold mb-2">
                          ❌ Error
                        </p>
                        <p className="text-sm text-red-500">{commentsError}</p>
                      </div>
                    ) : comments?.items?.length ? (
                      <div>
                        <div className="space-y-3 mb-4">
                          {comments.items.map((c) => (
                            <div
                              key={c.id}
                              className="bg-gray-50 p-4 rounded border"
                            >
                              <div className="flex items-start gap-2 mb-2 justify-between">
                                <span className="font-semibold text-sm">
                                  @{c.author}
                                </span>
                                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                  {c.sentiment}
                                </span>
                              </div>
                              <p className="text-sm text-gray-700 mb-2">
                                {truncateText(c.text, 200)}
                              </p>
                              <div className="text-xs text-gray-500 flex gap-4">
                                <span>👍 {c.like_count}</span>
                                {c.published_at && (
                                  <span>
                                    {new Date(
                                      c.published_at
                                    ).toLocaleDateString("id-ID")}
                                  </span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>

                        {comments.pagination.total_pages > 1 && (
                          <div className="flex items-center justify-center gap-3 pt-4 border-t">
                            <button
                              onClick={() =>
                                fetchComments(currentPage - 1, sentimentFilter)
                              }
                              disabled={currentPage === 1}
                              className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
                            >
                              ← Prev
                            </button>
                            <span className="text-sm font-semibold">
                              Halaman {currentPage}/
                              {comments.pagination.total_pages}
                            </span>
                            <button
                              onClick={() =>
                                fetchComments(currentPage + 1, sentimentFilter)
                              }
                              disabled={
                                currentPage === comments.pagination.total_pages
                              }
                              className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
                            >
                              Next →
                            </button>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-center text-gray-500 py-8">
                        Tidak ada komentar
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default VideoDetail;
