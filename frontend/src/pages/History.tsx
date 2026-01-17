import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Trash2,
  GitCompare,
  X,
  BarChart3,
  TrendingUp,
  Search,
  AlertTriangle,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { logoutApi } from "../api/auth.api";
import api from "../api/axios";

type HistoryItem = {
  id: string;
  title: string;
  date: string;
  positive: number;
  neutral: number;
  negative: number;
  channel: string;
  thumbnail?: string;
};

const History: React.FC = () => {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<string[]>([]);
  const [showCompare, setShowCompare] = useState(false);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [deleteModal, setDeleteModal] = useState<{
    show: boolean;
    videoId: string | null;
    videoTitle: string;
  }>({ show: false, videoId: null, videoTitle: "" });

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
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const response = await api.get("/analysis/history");
        const items = response.data?.items || [];
        setHistory(Array.isArray(items) ? items : []);
      } catch (error) {
        console.error("Failed to load history", error);
        setHistory([]);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((item) => item !== id);
      if (prev.length >= 2) return prev;
      return [...prev, id];
    });
  };

  const handleDelete = (videoId: string, videoTitle: string) => {
    setDeleteModal({ show: true, videoId, videoTitle });
  };

  const confirmDelete = async () => {
    if (!deleteModal.videoId) return;

    try {
      await api.delete(`/analysis/video/${deleteModal.videoId}`);
      // Remove from local state
      setHistory((prev) =>
        prev.filter((item) => item.id !== deleteModal.videoId)
      );
      // Remove from selected if it was selected
      setSelected((prev) => prev.filter((id) => id !== deleteModal.videoId));
      setDeleteModal({ show: false, videoId: null, videoTitle: "" });
    } catch (error) {
      const err = error as { response?: { data?: { detail?: string } } };
      alert(err?.response?.data?.detail || "Gagal menghapus analisis");
      console.error("Delete failed", err);
    }
  };

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

  const compareData = useMemo(() => {
    if (selected.length !== 2) return [];

    const first = history.find((item) => item.id === selected[0]);
    const second = history.find((item) => item.id === selected[1]);

    if (!first || !second) return [];

    return [
      {
        name: "Positif",
        [first.title.substring(0, 20) + "..."]: first.positive,
        [second.title.substring(0, 20) + "..."]: second.positive,
      },
      {
        name: "Netral",
        [first.title.substring(0, 20) + "..."]: first.neutral,
        [second.title.substring(0, 20) + "..."]: second.neutral,
      },
      {
        name: "Negatif",
        [first.title.substring(0, 20) + "..."]: first.negative,
        [second.title.substring(0, 20) + "..."]: second.negative,
      },
    ];
  }, [selected, history]);

  const comparisonInsights = useMemo(() => {
    if (selected.length !== 2) return null;

    const first = history.find((item) => item.id === selected[0]);
    const second = history.find((item) => item.id === selected[1]);

    if (!first || !second) return null;

    const winner = first.positive > second.positive ? first : second;
    const loser = first.positive > second.positive ? second : first;
    const diff = Math.abs(first.positive - second.positive);

    return {
      winner,
      loser,
      diff,
      winnerLabel: winner.title,
      positiveGap: diff,
      negativeComparison: winner.negative < loser.negative,
    };
  }, [selected, history]);

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
            className="flex items-center gap-3 text-blue-600 font-medium bg-blue-50 px-4 py-3 rounded-lg"
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

      {/* Main content */}
      <div className="flex-1 p-4 md:p-10 overflow-y-auto bg-linear-to-br from-blue-50/30 via-white to-purple-50/20">
        <div className="max-w-6xl mx-auto">
          <header className="flex flex-col md:flex-row justify-between items-start gap-4 mb-6 md:mb-10">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold text-gray-900">
                Riwayat Analisis
              </h2>
              <p className="text-gray-500 text-sm md:text-base">
                Pilih 2 video untuk membandingkan statistik sentimen
              </p>
            </div>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 w-full md:w-auto">
              <span className="text-xs md:text-sm font-medium text-gray-400 bg-white px-3 md:px-4 py-2 rounded-full border border-gray-100">
                {selected.length}/2 Terpilih
              </span>
              {selected.length === 2 && (
                <button
                  onClick={() => setShowCompare(true)}
                  className="w-full sm:w-auto bg-blue-600 text-white px-4 md:px-6 py-2 md:py-3 rounded-2xl font-bold flex items-center justify-center gap-2 hover:bg-blue-700 transition-all shadow-lg shadow-blue-200 text-sm md:text-base"
                >
                  <GitCompare size={18} /> Bandingkan
                </button>
              )}
            </div>
          </header>

          {/* Desktop Table View */}
          <div className="hidden md:block bg-white rounded-4xl shadow-sm border border-gray-100 overflow-x-auto">
            <table className="w-full text-left text-sm md:text-base">
              <thead className="bg-gray-50/50 sticky top-0">
                <tr>
                  <th className="p-3 md:p-6 text-xs font-black text-gray-400 uppercase tracking-widest whitespace-nowrap">
                    Pilih
                  </th>
                  <th className="p-3 md:p-6 text-xs font-black text-gray-400 uppercase tracking-widest whitespace-nowrap">
                    Detail Video
                  </th>
                  <th className="p-3 md:p-6 text-xs font-black text-gray-400 uppercase tracking-widest whitespace-nowrap">
                    Skor Sentimen
                  </th>
                  <th className="p-3 md:p-6 text-xs font-black text-gray-400 uppercase tracking-widest whitespace-nowrap">
                    Aksi
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {loading && history.length === 0 && (
                  <tr>
                    <td
                      colSpan={4}
                      className="p-3 md:p-6 text-center text-gray-500 text-sm"
                    >
                      Memuat riwayat...
                    </td>
                  </tr>
                )}
                {history.map((item) => (
                  <tr
                    key={item.id}
                    className={`hover:bg-blue-50/20 transition-all ${
                      selected.includes(item.id) ? "bg-blue-50/50" : ""
                    }`}
                  >
                    <td className="p-3 md:p-6">
                      <div className="relative flex items-center">
                        <input
                          type="checkbox"
                          className="w-5 h-5 md:w-6 md:h-6 rounded-lg border-gray-200 text-blue-600 focus:ring-blue-100 cursor-pointer"
                          checked={selected.includes(item.id)}
                          onChange={() => toggleSelect(item.id)}
                        />
                      </div>
                    </td>
                    <td className="p-3 md:p-6 flex items-center gap-2 md:gap-4">
                      <img
                        src={
                          item.thumbnail ||
                          "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&q=80&w=400"
                        }
                        className="w-16 h-10 md:w-20 md:h-12 object-cover rounded-lg shadow-sm shrink-0"
                        alt="thumb"
                      />
                      <div className="min-w-0">
                        <p className="font-bold text-gray-800 leading-tight text-sm md:text-base line-clamp-2">
                          {item.title}
                        </p>
                        <p className="text-xs text-blue-500 font-medium truncate">
                          {item.channel} •{" "}
                          {new Date(item.date).toLocaleDateString("id-ID")}
                        </p>
                      </div>
                    </td>
                    <td className="p-3 md:p-6">
                      <div className="flex items-center gap-2 md:gap-4">
                        <div className="flex-1 h-2 md:h-3 bg-gray-100 rounded-full overflow-hidden flex min-w-0">
                          <div
                            className="bg-green-500 h-full"
                            style={{ width: `${item.positive}%` }}
                          ></div>
                          <div
                            className="bg-yellow-400 h-full"
                            style={{ width: `${item.neutral}%` }}
                          ></div>
                          <div
                            className="bg-red-500 h-full"
                            style={{ width: `${item.negative}%` }}
                          ></div>
                        </div>
                        <span className="text-xs md:text-sm font-bold text-gray-700 shrink-0">
                          {item.positive}%+
                        </span>
                      </div>
                    </td>
                    <td className="p-3 md:p-6">
                      <div className="flex items-center gap-2 md:gap-4 justify-end flex-wrap">
                        <button
                          onClick={() => handleDelete(item.id, item.title)}
                          className="p-2 md:p-3 text-gray-400 hover:text-red-500 bg-gray-50 hover:bg-red-50 rounded-xl transition-all"
                          title="Hapus"
                        >
                          <Trash2 size={16} />
                        </button>
                        <Link
                          to={`/video/${item.id}`}
                          className="inline-flex items-center px-2 md:px-3 py-2 md:py-3 text-blue-600 hover:bg-blue-50 bg-gray-50 rounded-xl transition-all font-semibold text-xs md:text-sm whitespace-nowrap"
                          title="Lihat Detail"
                        >
                          Detail
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile Card View */}
          <div className="md:hidden space-y-3">
            {loading && history.length === 0 && (
              <div className="bg-white p-4 rounded-2xl border border-gray-100 text-center text-gray-500 text-sm">
                Memuat riwayat...
              </div>
            )}
            {history.map((item) => (
              <div
                key={item.id}
                className={`bg-white p-4 rounded-2xl border transition-all ${
                  selected.includes(item.id)
                    ? "border-blue-300 bg-blue-50"
                    : "border-gray-100"
                }`}
              >
                {/* Header dengan checkbox */}
                <div className="flex items-start gap-3 mb-3">
                  <input
                    type="checkbox"
                    className="w-5 h-5 rounded-lg border-gray-200 text-blue-600 focus:ring-blue-100 cursor-pointer mt-1"
                    checked={selected.includes(item.id)}
                    onChange={() => toggleSelect(item.id)}
                  />
                  <img
                    src={
                      item.thumbnail ||
                      "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&q=80&w=400"
                    }
                    className="w-20 h-12 object-cover rounded-lg shadow-sm shrink-0"
                    alt="thumb"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-gray-800 text-sm line-clamp-2">
                      {item.title}
                    </p>
                    <p className="text-xs text-blue-500 font-medium truncate">
                      {item.channel}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(item.date).toLocaleDateString("id-ID")}
                    </p>
                  </div>
                </div>

                {/* Sentimen Score Bar */}
                <div className="mb-3 px-1">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden flex">
                      <div
                        className="bg-green-500 h-full"
                        style={{ width: `${item.positive}%` }}
                      ></div>
                      <div
                        className="bg-yellow-400 h-full"
                        style={{ width: `${item.neutral}%` }}
                      ></div>
                      <div
                        className="bg-red-500 h-full"
                        style={{ width: `${item.negative}%` }}
                      ></div>
                    </div>
                  </div>
                  <div className="flex justify-between text-xs font-semibold text-gray-600">
                    <span>Positif: {item.positive}%</span>
                    <span>Netral: {item.neutral}%</span>
                    <span>Negatif: {item.negative}%</span>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDelete(item.id, item.title)}
                    className="flex-1 flex items-center justify-center gap-2 p-2 text-gray-600 hover:text-red-500 bg-gray-50 hover:bg-red-50 rounded-xl transition-all font-semibold text-xs"
                  >
                    <Trash2 size={16} /> Hapus
                  </button>
                  <Link
                    to={`/video/${item.id}`}
                    className="flex-1 flex items-center justify-center gap-2 p-2 text-blue-600 hover:bg-blue-50 bg-gray-50 rounded-xl transition-all font-semibold text-xs"
                  >
                    Lihat Detail
                  </Link>
                </div>
              </div>
            ))}
          </div>

          {showCompare && selected.length === 2 && comparisonInsights && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/70 backdrop-blur-md">
              <div className="bg-white w-full max-w-5xl rounded-[40px] shadow-2xl p-6 md:p-10 max-h-[90vh] overflow-y-auto animate-in zoom-in duration-300">
                <div className="flex justify-between items-start md:items-center mb-6 md:mb-8 gap-4">
                  <div className="flex items-center gap-3 flex-1">
                    <div className="p-3 md:p-4 bg-linear-to-br from-blue-500 to-blue-600 text-white rounded-2xl shadow-lg shadow-blue-200">
                      <GitCompare size={24} />
                    </div>
                    <div>
                      <h3 className="text-2xl md:text-3xl font-bold text-gray-900">
                        Perbandingan Analisis
                      </h3>
                      <p className="text-sm text-gray-500 mt-1">
                        Evaluasi sentimen antara 2 video
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowCompare(false)}
                    className="p-2 hover:bg-gray-100 rounded-xl transition-all text-gray-400 hover:text-gray-600 shrink-0"
                  >
                    <X size={28} />
                  </button>
                </div>

                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                  <div className="bg-linear-to-br from-green-50 to-green-100 p-5 rounded-3xl border border-green-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-green-600 uppercase tracking-wider">
                        Positif
                      </span>
                      <TrendingUp size={18} className="text-green-600" />
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-black text-green-700">
                        {comparisonInsights.winner.positive}%
                      </span>
                      <span className="text-sm text-green-600">
                        vs {comparisonInsights.loser.positive}%
                      </span>
                    </div>
                    <p className="text-xs text-green-700 mt-2 font-medium">
                      Selisih +{comparisonInsights.diff}%
                    </p>
                  </div>

                  <div className="bg-linear-to-br from-yellow-50 to-yellow-100 p-5 rounded-3xl border border-yellow-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-yellow-600 uppercase tracking-wider">
                        Netral
                      </span>
                      <BarChart3 size={18} className="text-yellow-600" />
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-black text-yellow-700">
                        {comparisonInsights.winner.neutral}%
                      </span>
                      <span className="text-sm text-yellow-600">
                        vs {comparisonInsights.loser.neutral}%
                      </span>
                    </div>
                  </div>

                  <div className="bg-linear-to-br from-red-50 to-red-100 p-5 rounded-3xl border border-red-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-red-600 uppercase tracking-wider">
                        Negatif
                      </span>
                      <TrendingUp
                        size={18}
                        className="text-red-600 rotate-180"
                      />
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-black text-red-700">
                        {comparisonInsights.winner.negative}%
                      </span>
                      <span className="text-sm text-red-600">
                        vs {comparisonInsights.loser.negative}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Chart */}
                <div className="bg-gray-50 rounded-3xl p-6 mb-8">
                  <h4 className="text-lg font-bold text-gray-800 mb-6">
                    Grafik Perbandingan
                  </h4>
                  <div className="h-80 md:h-96 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={compareData}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid
                          strokeDasharray="3 3"
                          vertical={false}
                          stroke="#e2e8f0"
                        />
                        <XAxis
                          dataKey="name"
                          axisLine={false}
                          tickLine={false}
                          tick={{
                            fill: "#64748b",
                            fontSize: 14,
                            fontWeight: 600,
                          }}
                          dy={10}
                        />
                        <YAxis
                          axisLine={false}
                          tickLine={false}
                          tick={{ fill: "#64748b", fontSize: 12 }}
                          label={{
                            value: "Persentase (%)",
                            angle: -90,
                            position: "insideLeft",
                            fill: "#64748b",
                          }}
                        />
                        <Tooltip
                          contentStyle={{
                            borderRadius: "16px",
                            border: "none",
                            boxShadow: "0 10px 25px -5px rgba(0,0,0,0.1)",
                            padding: "12px",
                          }}
                          cursor={{ fill: "#f1f5f9", radius: 8 }}
                        />
                        <Legend
                          wrapperStyle={{ paddingTop: "24px" }}
                          iconType="circle"
                        />
                        {compareData.length > 0 && (
                          <>
                            <Bar
                              dataKey={Object.keys(compareData[0])[1]}
                              fill="#3B82F6"
                              radius={[8, 8, 0, 0]}
                              maxBarSize={80}
                            />
                            <Bar
                              dataKey={Object.keys(compareData[0])[2]}
                              fill="#93C5FD"
                              radius={[8, 8, 0, 0]}
                              maxBarSize={80}
                            />
                          </>
                        )}
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Insights */}
                <div className="bg-linear-to-br from-blue-50 to-blue-100 p-6 rounded-3xl border-2 border-blue-200 mb-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-blue-600 text-white rounded-xl">
                      <TrendingUp size={20} />
                    </div>
                    <h4 className="font-bold text-blue-900 text-lg">
                      🏆 Pemenang Sentimen
                    </h4>
                  </div>
                  <p className="text-blue-800 text-sm leading-relaxed mb-3">
                    <strong className="font-bold">
                      {comparisonInsights.winnerLabel}
                    </strong>{" "}
                    unggul dengan{" "}
                    <span className="font-bold text-blue-900">
                      {comparisonInsights.positiveGap}%
                    </span>{" "}
                    lebih banyak sentimen positif.
                  </p>
                  <div className="bg-white/60 backdrop-blur-sm p-3 rounded-xl">
                    <p className="text-xs text-blue-700 font-medium">
                      ✓ Sentimen positif: {comparisonInsights.winner.positive}
                      %<br />✓ Sentimen negatif:{" "}
                      {comparisonInsights.winner.negative}%
                      {comparisonInsights.negativeComparison &&
                        " (Lebih rendah!)"}
                    </p>
                  </div>
                </div>

                {/* Video Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8 pt-8 border-t border-gray-200">
                  {[comparisonInsights.winner, comparisonInsights.loser].map(
                    (item) => (
                      <div
                        key={item.id}
                        className="bg-white p-4 rounded-2xl border-2 border-gray-100 hover:border-blue-200 transition-all"
                      >
                        <div className="flex gap-3 mb-3">
                          <img
                            src={
                              item.thumbnail ||
                              "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&q=80&w=400"
                            }
                            className="w-24 h-16 object-cover rounded-xl"
                            alt="thumb"
                          />
                          <div className="flex-1 min-w-0">
                            <p className="font-bold text-sm text-gray-900 line-clamp-2 mb-1">
                              {item.title}
                            </p>
                            <p className="text-xs text-blue-600 font-medium">
                              {item.channel}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-2 text-xs font-semibold">
                          <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full">
                            +{item.positive}%
                          </span>
                          <span className="bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full">
                            {item.neutral}%
                          </span>
                          <span className="bg-red-100 text-red-700 px-3 py-1 rounded-full">
                            -{item.negative}%
                          </span>
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Delete Confirmation Modal */}
          {deleteModal.show && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/70 backdrop-blur-md animate-in fade-in duration-200">
              <div className="bg-white w-full max-w-md rounded-3xl shadow-2xl p-6 md:p-8 animate-in zoom-in duration-300">
                <div className="flex flex-col items-center text-center">
                  {/* Icon */}
                  <div className="w-16 h-16 md:w-20 md:h-20 rounded-full bg-red-100 flex items-center justify-center mb-4">
                    <AlertTriangle className="text-red-600" size={32} />
                  </div>

                  {/* Title */}
                  <h3 className="text-xl md:text-2xl font-bold text-gray-900 mb-2">
                    Hapus Analisis?
                  </h3>

                  {/* Description */}
                  <p className="text-sm md:text-base text-gray-600 mb-2">
                    Anda akan menghapus analisis untuk:
                  </p>
                  <p className="text-sm font-semibold text-gray-800 mb-6 line-clamp-2 px-4">
                    "{deleteModal.videoTitle}"
                  </p>
                  <p className="text-xs md:text-sm text-red-600 font-medium mb-8">
                    ⚠️ Tindakan ini tidak dapat dibatalkan
                  </p>

                  {/* Buttons */}
                  <div className="flex gap-3 w-full">
                    <button
                      onClick={() =>
                        setDeleteModal({
                          show: false,
                          videoId: null,
                          videoTitle: "",
                        })
                      }
                      className="flex-1 px-4 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold rounded-xl transition-all"
                    >
                      Batal
                    </button>
                    <button
                      onClick={confirmDelete}
                      className="flex-1 px-4 py-3 bg-linear-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white font-bold rounded-xl transition-all shadow-lg shadow-red-200 flex items-center justify-center gap-2"
                    >
                      <Trash2 size={18} />
                      Hapus
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default History;
