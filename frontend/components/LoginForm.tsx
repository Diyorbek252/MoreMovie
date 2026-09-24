"use client";

/** `users/login.html` DRF/Next ekvivalenti — `LoginForm` (Django) validatsiya
 * xabarlarini o'zbekchada to'g'ridan-to'g'ri ko'rsatadi. */

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiClientError, apiPost, ensureCsrfCookie } from "@/lib/api-client";

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    ensureCsrfCookie();
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPending(true);
    setError(null);
    try {
      await apiPost("/api/v1/auth/login/", { username, password, remember_me: rememberMe });
      const next = searchParams.get("next") || "/";
      router.push(next);
      router.refresh();
    } catch (err) {
      setError((err as ApiClientError).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="stack" onSubmit={onSubmit}>
      {error && (
        <div className="alert alert--error" role="alert">
          {error}
        </div>
      )}

      <div className="field">
        <label className="field__label" htmlFor="username">
          Username yoki email
        </label>
        <input
          className="input"
          id="username"
          type="text"
          placeholder="username yoki email@misol.uz"
          autoComplete="username"
          autoFocus
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
      </div>

      <div className="field">
        <label className="field__label" htmlFor="password">
          Parol
        </label>
        <input
          className="input"
          id="password"
          type="password"
          placeholder="Parolingiz"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>

      <label className="row" style={{ gap: "var(--s-2)" }}>
        <input type="checkbox" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} />
        Meni eslab qol
      </label>

      <button className="btn btn--primary btn--block" type="submit" disabled={pending}>
        {pending ? "Kirilmoqda..." : "Kirish"}
      </button>
    </form>
  );
}
