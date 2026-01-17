import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Youtube,
  ThumbsUp,
  MessageCircle,
  Search,
  BarChart3,
  Sparkles,
  TrendingUp,
  Clock,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from "recharts";
import { logoutApi } from "../api/auth.api";
import api from "../api/axios";

type PercentEntry = { name: string; value: number; color: string };
type AnalysisResult = {
  videoInfo: {
    title: string;
    channel: string;
    thumbnail: string;
    likes: string;
    totalComments: number;
  };
  sentiment: {
    positive: number;
    neutral: number;
    negative: number;
    percentages: PercentEntry[];
  };
  insight: string;
  analysisId?: string;
  savedAt?: string;
};

const Dashboard: React.FC = () => {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string>("");
  const navigate = useNavigate();

  // Check authentication on mount
  useEffect(() => {
    const token =
      localStorage.getItem("accessToken") || localStorage.getItem("token");
    if (!token) {
      navigate("/login");
      return;
    }
  }, [navigate]);

  // Rehydrate last analysis on mount
  useEffect(() => {
    try {
      const rawResult = localStorage.getItem("last_analysis_result");
      if (rawResult) {
        const parsed = JSON.parse(rawResult);
        if (parsed && typeof parsed === "object") {
          setResult(parsed);
        }
      }
      const savedUrl = localStorage.getItem("last_analysis_url");
      if (savedUrl) setUrl(savedUrl);
    } catch (err) {
      console.warn("Rehydrate failed", err);
    }
  }, []);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.post("/analysis/", { youtube_url: url });
      const data = res.data;
      const toNumber = (v: unknown) => {
        const n = Number(v);
        return Number.isFinite(n) ? n : 0;
      };

      const total = toNumber(data.total_comments);
      const pos = toNumber(data.sentiment_distribution?.positive);
      const neu = toNumber(data.sentiment_distribution?.neutral);
      const neg = toNumber(data.sentiment_distribution?.negative);

      const pct = (v: number) =>
        total > 0 ? Math.round((v / total) * 100) : 0;

      const likesRaw = data.video?.like_count as number | string | undefined;
      const likesNum = typeof likesRaw === "number" ? likesRaw : undefined;
      const likesStr =
        likesNum !== undefined
          ? likesNum.toLocaleString("id-ID")
          : typeof likesRaw === "string"
          ? likesRaw
          : "-";

      const mapped = {
        videoInfo: {
          title: data.video?.title ?? "",
          channel: data.video?.channel ?? "",
          thumbnail:
            data.video?.thumbnail_url ??
            "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&q=80&w=400", // fallback
          likes: likesStr,
          totalComments: total,
        },
        sentiment: {
          positive: pos,
          neutral: neu,
          negative: neg,
          percentages: [
            { name: "Positif", value: pct(pos), color: "#10B981" },
            { name: "Netral", value: pct(neu), color: "#F59E0B" },
            { name: "Negatif", value: pct(neg), color: "#EF4444" },
          ],
        },
        insight: `Hasil analisis: Positif ${pct(pos)}%, Netral ${pct(
          neu
        )}%, Negatif ${pct(neg)}% dari ${total} komentar.`,
        analysisId: data.analysis_id,
        savedAt: new Date().toISOString(),
      };
      setResult(mapped);
      try {
        localStorage.setItem("last_analysis_result", JSON.stringify(mapped));
        localStorage.setItem("last_analysis_url", url);
      } catch (err) {
        // Ignore storage quota or serialization errors
        console.warn("Persist result failed", err);
      }
      // persist last error is not necessary
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } };
      const msg = error?.response?.data?.detail || "Analisis gagal";
      setError(msg);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logoutApi();
    } catch (_e) {
      // ignore errors; client-side logout is enough
      console.warn("Logout API failed", _e);
    }
    localStorage.removeItem("token");
    localStorage.removeItem("last_analysis_result");
    localStorage.removeItem("last_analysis_url");
    navigate("/login");
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
            className="flex items-center gap-3 text-blue-600 font-medium bg-blue-50 px-4 py-3 rounded-lg"
          >
            <Search size={18} /> Analisis
          </a>
          <a
            href="/history"
            className="flex items-center gap-3 text-gray-600 hover:bg-gray-100 px-4 py-3 rounded-lg transition"
          >
            <BarChart3 size={18} /> Riwayat
          </a>
        </nav>
        <button
          onClick={handleLogout}
          className="hidden md:block w-full mt-8 text-red-600 hover:bg-red-50 px-4 py-3 rounded-lg font-medium transition"
        >
          Logout
        </button>
      </div>

      <div className="flex-1 p-6 md:p-12 overflow-y-auto bg-linear-to-br from-blue-50/30 via-white to-purple-50/20">
        <div className="max-w-4xl mx-auto">
          {!result ? (
            <div className="pt-12 pb-12">
              {/* Hero dengan badge */}
              <div className="text-center mb-8">
                <h2 className="text-4xl font-bold text-gray-900 mb-3">
                  Analisis Video YouTube
                </h2>
                <p className="text-gray-600 mb-8">
                  Pahami sentimen komentar dengan cepat dan akurat
                </p>
              </div>

              <div className="max-w-xl mx-auto mb-12">
                <form onSubmit={handleAnalyze} className="space-y-3">
                  <div className="relative">
                    <Youtube
                      className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                      size={20}
                    />
                    <input
                      type="text"
                      placeholder="Masukkan link video YouTube"
                      className="w-full pl-12 pr-4 py-3.5 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 transition"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                    />
                  </div>
                  <button
                    disabled={loading}
                    className={`w-full bg-blue-600 hover:bg-blue-700 text-white py-3.5 rounded-lg font-medium transition shadow-sm hover:shadow-md ${
                      loading ? "opacity-70" : ""
                    }`}
                  >
                    {loading ? "Menganalisis..." : "Analisis"}
                  </button>
                </form>
                {error && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-600 text-sm">{error}</p>
                  </div>
                )}
              </div>

              {/* Info Cards - Simple & Clean */}
              <div className="max-w-3xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center shrink-0">
                      <Sparkles className="text-blue-600" size={18} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 text-sm mb-1">
                        Analisis AI
                      </h3>
                      <p className="text-gray-600 text-xs">
                        Klasifikasi sentimen otomatis
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center shrink-0">
                      <TrendingUp className="text-green-600" size={18} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 text-sm mb-1">
                        Akurat
                      </h3>
                      <p className="text-gray-600 text-xs">
                        Model terlatih presisi tinggi
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center shrink-0">
                      <Clock className="text-purple-600" size={18} />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 text-sm mb-1">
                        Cepat
                      </h3>
                      <p className="text-gray-600 text-xs">
                        Hasil dalam hitungan detik
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <>
              <div className="mb-6 flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-900">
                  Hasil Analisis
                </h2>
                <button
                  onClick={() => {
                    setResult(null);
                    setUrl("");
                    setError("");
                  }}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                >
                  ← Analisis Baru
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-4">
                  {/* Video Card */}
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
                    <img
                      src={result.videoInfo.thumbnail}
                      className="w-full h-44 object-cover rounded-lg mb-4"
                      alt="thumbnail"
                    />
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {result.videoInfo.title}
                    </h3>
                    <p className="text-gray-600 mb-3 text-sm">
                      {result.videoInfo.channel}
                    </p>
                    <div className="flex gap-6 text-gray-500 text-sm">
                      <div className="flex items-center gap-2">
                        <ThumbsUp size={16} /> {result.videoInfo.likes}
                      </div>
                      <div className="flex items-center gap-2">
                        <MessageCircle size={16} />{" "}
                        {result.videoInfo.totalComments}
                      </div>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      {
                        label: "Positif",
                        val: result.sentiment.positive,
                        color: "text-green-600",
                        bg: "bg-green-50",
                      },
                      {
                        label: "Netral",
                        val: result.sentiment.neutral,
                        color: "text-yellow-600",
                        bg: "bg-yellow-50",
                      },
                      {
                        label: "Negatif",
                        val: result.sentiment.negative,
                        color: "text-red-600",
                        bg: "bg-red-50",
                      },
                    ].map((stat, i) => (
                      <div
                        key={i}
                        className={`${
                          stat.bg
                        } p-5 rounded-lg text-center border ${stat.bg.replace(
                          "50",
                          "100"
                        )}`}
                      >
                        <p className={`text-2xl font-bold ${stat.color} mb-1`}>
                          {stat.val}
                        </p>
                        <p className="text-xs text-gray-600">{stat.label}</p>
                      </div>
                    ))}
                  </div>

                  {/* Insight */}
                  <div className="bg-blue-50 border border-blue-100 p-4 rounded-lg">
                    <p className="text-gray-700 text-sm">{result.insight}</p>
                  </div>
                </div>

                {/* Chart */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-5">
                  <h4 className="font-semibold text-gray-900 mb-4 text-sm">
                    Distribusi Sentimen
                  </h4>
                  <div className="h-56">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={result.sentiment.percentages}
                          innerRadius={45}
                          outerRadius={75}
                          paddingAngle={2}
                          dataKey="value"
                        >
                          {result.sentiment.percentages.map(
                            (entry: PercentEntry, index: number) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            )
                          )}
                        </Pie>
                        <Tooltip formatter={(val) => `${val}%`} />
                        <Legend formatter={(value) => value} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
