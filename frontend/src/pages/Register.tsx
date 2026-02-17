import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { meApi, registerApi } from "../api/auth.api";
import { Mail, Lock, User, Eye, EyeOff, UserPlus } from "lucide-react";

const Register: React.FC = () => {
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const navigate = useNavigate();

  const hasPassword = formData.password.length > 0;
  const passwordChecks = {
    length: formData.password.length >= 8,
    upper: /[A-Z]/.test(formData.password),
    lower: /[a-z]/.test(formData.password),
    digit: /\d/.test(formData.password),
  };
  const ruleTextClass = (ok: boolean) =>
    ok ? "text-green-700" : hasPassword ? "text-red-600" : "text-gray-500";
  const ruleDotClass = (ok: boolean) =>
    ok ? "bg-green-600" : hasPassword ? "bg-red-500" : "bg-gray-300";

  const normalizeRegisterError = (detail: unknown) => {
    if (!detail) return "Registrasi gagal. Coba lagi nanti.";
    if (Array.isArray(detail)) {
      const first = detail[0] as { msg?: string } | undefined;
      if (first?.msg) return normalizeRegisterError(first.msg);
    }
    const message = String(detail);
    const lower = message.toLowerCase();
    if (lower.includes("email already registered")) {
      return "Email sudah terdaftar";
    }
    if (
      lower.includes("not a valid email") ||
      lower.includes("value is not a valid email")
    ) {
      return "Format email tidak valid";
    }
    if (lower.includes("password must be at least 8")) {
      return "Password minimal 8 karakter";
    }
    if (lower.includes("uppercase letter")) {
      return "Password harus mengandung minimal 1 huruf besar";
    }
    if (lower.includes("lowercase letter")) {
      return "Password harus mengandung minimal 1 huruf kecil";
    }
    if (lower.includes("digit")) {
      return "Password harus mengandung minimal 1 angka";
    }
    if (lower.includes("full name") && lower.includes("invalid")) {
      return "Nama tidak valid";
    }
    if (lower.includes("database error")) {
      return "Terjadi kesalahan database. Coba lagi nanti.";
    }
    if (lower.includes("registration failed")) {
      return "Registrasi gagal. Coba lagi nanti.";
    }
    return "Registrasi gagal. Coba lagi nanti.";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!formData.email) {
      setError("Email diperlukan");
      return;
    }
    if (!formData.username) {
      setError("Username diperlukan");
      return;
    }
    if (formData.password.length < 8) {
      setError("Password minimal 8 karakter");
      return;
    }
    if (!/[A-Z]/.test(formData.password)) {
      setError("Password harus mengandung minimal 1 huruf besar");
      return;
    }
    if (!/[a-z]/.test(formData.password)) {
      setError("Password harus mengandung minimal 1 huruf kecil");
      return;
    }
    if (!/\d/.test(formData.password)) {
      setError("Password harus mengandung minimal 1 angka");
      return;
    }
    if (formData.password !== formData.confirmPassword) {
      setError("Password tidak cocok!");
      return;
    }

    setLoading(true);
    try {
      // Backend menerima full_name, gunakan username sebagai full_name
      const response = await registerApi(
        formData.email,
        formData.username,
        formData.password,
      );

      const token = response?.data?.access_token;
      if (!token) {
        setError("Registrasi berhasil, tetapi token tidak ditemukan.");
        return;
      }

      localStorage.setItem("token", token);

      try {
        await meApi();
      } catch (verifyErr) {
        localStorage.removeItem("token");
        setError(
          "Registrasi berhasil, tetapi sesi tidak valid. Silakan login ulang.",
        );
        return;
      }

      navigate("/");
    } catch (err: any) {
      const msg = normalizeRegisterError(
        err?.response?.data?.detail ?? err?.message,
      );
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-100 via-blue-50 to-white flex items-center justify-center p-4 font-sans text-gray-900">
      <div className="w-full max-w-[1000px] grid grid-cols-1 md:grid-cols-2 bg-white rounded-3xl shadow-2xl overflow-hidden min-h-[650px]">
        {/* Sisi Kiri: Branding (Identik dengan Login) */}
        <div className="hidden md:flex bg-blue-600 p-12 flex-col justify-between text-white relative overflow-hidden">
          <div className="relative z-10">
            <h1 className="text-4xl font-bold mb-4 leading-tight">
              Mulai Perjalanan Analisis Anda.
            </h1>
            <p className="text-blue-100 text-lg">
              Dapatkan wawasan mendalam dari ribuan komentar YouTube secara
              instan.
            </p>
          </div>

          <div className="relative z-10 bg-white/10 backdrop-blur-lg border border-white/20 p-6 rounded-2xl">
            <h3 className="font-bold text-lg mb-4">Fitur Unggulan:</h3>
            <div className="space-y-3">
              <div className="flex items-start gap-2">
                <span className="text-xl">✅</span>
                <p className="text-sm">Analisis sentimen otomatis dengan AI</p>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-xl">📈</span>
                <p className="text-sm">Statistik lengkap & grafik interaktif</p>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-xl">🔒</span>
                <p className="text-sm">Data aman & terenkripsi</p>
              </div>
            </div>
          </div>

          {/* Efek Blob background */}
          <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-blue-500 rounded-full filter blur-3xl opacity-50 animate-blob"></div>
        </div>

        {/* Sisi Kanan: Form Register */}
        <div className="p-8 md:p-14 flex flex-col justify-center bg-white">
          <div className="mb-8 text-center md:text-left">
            <h2 className="text-3xl font-extrabold tracking-tight">
              Daftar Akun 🚀
            </h2>
            <p className="text-gray-500 mt-2">
              Lengkapi data di bawah untuk bergabung
            </p>
          </div>

          <form className="space-y-4" onSubmit={handleSubmit}>
            {/* Username */}
            <div className="space-y-1">
              <label className="text-sm font-semibold text-gray-700 ml-1">
                Username
              </label>
              <div className="relative group">
                <User
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-600 transition-colors"
                  size={20}
                />
                <input
                  type="text"
                  required
                  className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-600 focus:bg-white outline-none transition-all"
                  placeholder="joe_sentimen"
                  onChange={(e) =>
                    setFormData({ ...formData, username: e.target.value })
                  }
                />
              </div>
            </div>

            {/* Email */}
            <div className="space-y-1">
              <label className="text-sm font-semibold text-gray-700 ml-1">
                Email Address
              </label>
              <div className="relative group">
                <Mail
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-600 transition-colors"
                  size={20}
                />
                <input
                  type="email"
                  required
                  className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-600 focus:bg-white outline-none transition-all"
                  placeholder="name@example.com"
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                />
              </div>
            </div>

            {/* Password */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-sm font-semibold text-gray-700 ml-1">
                  Password
                </label>
                <div className="relative">
                  <Lock
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                    size={18}
                  />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-600 outline-none transition-all"
                    placeholder="••••••••"
                    onChange={(e) =>
                      setFormData({ ...formData, password: e.target.value })
                    }
                  />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-sm font-semibold text-gray-700 ml-1">
                  Konfirmasi
                </label>
                <div className="relative">
                  <Lock
                    className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
                    size={18}
                  />
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    className="w-full pl-11 pr-10 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-600 outline-none transition-all"
                    placeholder="••••••••"
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        confirmPassword: e.target.value,
                      })
                    }
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>
            </div>

            <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-xs">
              <p className="font-semibold mb-2 text-blue-700">
                Syarat password:
              </p>
              <ul className="space-y-1">
                <li
                  className={`flex items-center gap-2 ${ruleTextClass(
                    passwordChecks.length,
                  )}`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${ruleDotClass(
                      passwordChecks.length,
                    )}`}
                  />
                  Minimal 8 karakter
                </li>
                <li
                  className={`flex items-center gap-2 ${ruleTextClass(
                    passwordChecks.upper,
                  )}`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${ruleDotClass(
                      passwordChecks.upper,
                    )}`}
                  />
                  Minimal 1 huruf besar
                </li>
                <li
                  className={`flex items-center gap-2 ${ruleTextClass(
                    passwordChecks.lower,
                  )}`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${ruleDotClass(
                      passwordChecks.lower,
                    )}`}
                  />
                  Minimal 1 huruf kecil
                </li>
                <li
                  className={`flex items-center gap-2 ${ruleTextClass(
                    passwordChecks.digit,
                  )}`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${ruleDotClass(
                      passwordChecks.digit,
                    )}`}
                  />
                  Minimal 1 angka
                </li>
              </ul>
            </div>

            <button
              type="submit"
              className="w-full mt-2 bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-200 flex items-center justify-center gap-2 group transition-all active:scale-[0.98] disabled:opacity-60"
              disabled={loading}
            >
              {loading ? "Memproses..." : "Daftar Sekarang"}
              <UserPlus
                className="group-hover:rotate-12 transition-transform"
                size={20}
              />
            </button>

            {error && (
              <p className="mt-4 text-center text-red-600 text-sm font-semibold">
                {error}
              </p>
            )}
          </form>

          <p className="mt-8 text-center text-gray-600 text-sm">
            Sudah memiliki akun?{" "}
            <a
              href="/login"
              className="text-blue-600 font-bold hover:underline"
            >
              Login di sini
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
