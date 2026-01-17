import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginApi, meApi, googleLoginApi } from "../api/auth.api";
import { Mail, Lock, Eye, EyeOff, ArrowRight } from "lucide-react";

const Login: React.FC = () => {
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const navigate = useNavigate();
  const googleBtnRef = useRef<HTMLDivElement>(null);
  const [googleReady, setGoogleReady] = useState<boolean>(false);

  useEffect(() => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
    let tries = 0;
    const maxTries = 30; // ~7.5 detik dengan interval 250ms

    const init = () => {
      const g = (window as any).google;
      if (!clientId || !g?.accounts?.id || !googleBtnRef.current) return false;
      try {
        g.accounts.id.initialize({
          client_id: clientId,
          callback: async (response: any) => {
            const idToken = response?.credential;
            if (!idToken) return;
            try {
              const res = await googleLoginApi(idToken);
              const data = res.data;
              if (data?.access_token) {
                localStorage.setItem("token", data.access_token);
                navigate("/");
              }
            } catch (err) {
              console.error("Google login gagal", err);
            }
          },
        });
        g.accounts.id.renderButton(googleBtnRef.current, {
          theme: "outline",
          size: "large",
          text: "continue_with",
          shape: "rectangular",
          logo_alignment: "left",
        });
        setGoogleReady(true);
        return true;
      } catch (e) {
        console.warn("GSI init gagal", e);
        return false;
      }
    };

    if (!init()) {
      const id = setInterval(() => {
        tries += 1;
        if (init() || tries >= maxTries) {
          clearInterval(id);
        }
      }, 250);
      return () => clearInterval(id);
    }
  }, [navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await loginApi(email, password);
      const data = res.data;
      if (data?.access_token) {
        localStorage.setItem("token", data.access_token);
        // optional: verify token by calling /auth/me
        try {
          await meApi();
        } catch {}
        navigate("/");
      } else {
        setError("Login gagal: token tidak ditemukan");
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "Login gagal";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-blue-100 via-blue-50 to-white flex items-center justify-center p-4 font-sans text-gray-900">
      <div className="w-full max-w-[1000px] grid grid-cols-1 md:grid-cols-2 bg-white rounded-3xl shadow-2xl overflow-hidden min-h-[600px]">
        {/* Sisi Kiri: Branding (PC Only) */}
        <div className="hidden md:flex bg-blue-600 p-12 flex-col justify-between text-white relative overflow-hidden">
          <div className="relative z-10">
            <h1 className="text-4xl font-bold mb-4 leading-tight">
              Analisis Sentimen Jadi Lebih Mudah.
            </h1>
            <p className="text-blue-100 text-lg">
              Pantau opini publik dari komentar YouTube dalam hitungan detik
              dengan AI.
            </p>
          </div>

          <div className="relative z-10 space-y-4">
            <div className="bg-white/10 backdrop-blur-lg border border-white/20 p-4 rounded-xl">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">🎯</span>
                </div>
                <div>
                  <p className="font-bold text-lg">Akurat & Cepat</p>
                  <p className="text-sm text-blue-100">
                    Analisis ribuan komentar dalam hitungan detik
                  </p>
                </div>
              </div>
            </div>
            <div className="bg-white/10 backdrop-blur-lg border border-white/20 p-4 rounded-xl">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                  <span className="text-2xl">📊</span>
                </div>
                <div>
                  <p className="font-bold text-lg">Visualisasi Menarik</p>
                  <p className="text-sm text-blue-100">
                    Dashboard interaktif & mudah dipahami
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sisi Kanan: Form */}
        <div className="p-8 md:p-14 flex flex-col justify-center bg-white">
          <div className="mb-10 text-center md:text-left">
            <h2 className="text-3xl font-extrabold tracking-tight">
              Selamat Datang 👋
            </h2>
            <p className="text-gray-500 mt-2">Silakan masuk ke akun Anda</p>
          </div>

          <form className="space-y-6" onSubmit={handleLogin}>
            <div className="space-y-2">
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
                  value={email}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setEmail(e.target.value)
                  }
                  placeholder="name@example.com"
                  className="w-full pl-12 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-600 focus:bg-white outline-none transition-all"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center ml-1">
                <label className="text-sm font-semibold text-gray-700">
                  Password
                </label>
                <a
                  href="#"
                  className="text-xs font-bold text-blue-600 hover:text-blue-800"
                >
                  Lupa Password?
                </a>
              </div>
              <div className="relative group">
                <Lock
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-600 transition-colors"
                  size={20}
                />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setPassword(e.target.value)
                  }
                  placeholder="••••••••"
                  className="w-full pl-12 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-4 focus:ring-blue-100 focus:border-blue-600 focus:bg-white outline-none transition-all"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl shadow-lg shadow-blue-200 flex items-center justify-center gap-2 group transition-all active:scale-[0.98] disabled:opacity-60"
              disabled={loading}
            >
              {loading ? "Memproses..." : "Masuk Sekarang"}
              <ArrowRight
                className="group-hover:translate-x-1 transition-transform"
                size={20}
              />
            </button>

            {error && (
              <p className="mt-4 text-center text-red-600 text-sm font-semibold">
                {error}
              </p>
            )}
          </form>

          <div className="relative my-8 text-center">
            <hr className="border-gray-100" />
            <span className="absolute left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white px-4 text-sm text-gray-400 font-medium">
              Atau
            </span>
          </div>

          <div
            ref={googleBtnRef}
            className="w-full flex items-center justify-center"
          />
          {!googleReady && (
            <div className="mt-3 text-center text-xs text-gray-500">
              Menyiapkan Google Sign-In... Pastikan VITE_GOOGLE_CLIENT_ID ada di
              frontend/.env lalu reload.
            </div>
          )}

          <p className="mt-10 text-center text-gray-600 text-sm">
            Belum punya akun?{" "}
            <a
              href="/register"
              className="text-blue-600 font-bold hover:underline"
            >
              Daftar Gratis
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
