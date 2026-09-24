"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiPost, ensureCsrfCookie } from "@/lib/api-client";
import type { ApiErrorPayload } from "@/lib/types";

export default function RegisterForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password1, setPassword1] = useState("");
  const [password2, setPassword2] = useState("");
  const [errors, setErrors] = useState<ApiErrorPayload | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    ensureCsrfCookie();
  }, []);

  function fieldError(field: string) {
    const value = errors?.[field];
    if (!value) return null;
    return Array.isArray(value) ? value[0] : value;
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setPending(true);
    setErrors(null);
    try {
      await apiPost("/api/v1/auth/register/", { username, email, password1, password2 });
      router.push("/");
      router.refresh();
    } catch (err) {
      setErrors((err as { payload: ApiErrorPayload }).payload);
    } finally {
      setPending(false);
    }
  }

  const nonField = fieldError("non_field_errors") || fieldError("detail");

  return (
    <form className="stack" onSubmit={onSubmit}>
      {nonField && (
        <div className="alert alert--error" role="alert">
          {nonField}
        </div>
      )}

      <div className="field">
        <label className="field__label" htmlFor="username">
          Foydalanuvchi nomi
        </label>
        <input
          className="input"
          id="username"
          placeholder="foydalanuvchi_nomi"
          autoComplete="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        {fieldError("username") && <p className="field__help" style={{ color: "var(--red)" }}>{fieldError("username")}</p>}
      </div>

      <div className="field">
        <label className="field__label" htmlFor="email">
          Email
        </label>
        <input
          className="input"
          id="email"
          type="email"
          placeholder="email@misol.uz"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        {fieldError("email") && <p className="field__help" style={{ color: "var(--red)" }}>{fieldError("email")}</p>}
      </div>

      <div className="field">
        <label className="field__label" htmlFor="password1">
          Parol
        </label>
        <input
          className="input"
          id="password1"
          type="password"
          placeholder="Kamida 8 ta belgi"
          autoComplete="new-password"
          value={password1}
          onChange={(e) => setPassword1(e.target.value)}
          required
        />
        {fieldError("password1") && <p className="field__help" style={{ color: "var(--red)" }}>{fieldError("password1")}</p>}
      </div>

      <div className="field">
        <label className="field__label" htmlFor="password2">
          Parolni tasdiqlang
        </label>
        <input
          className="input"
          id="password2"
          type="password"
          placeholder="Parolni takrorlang"
          autoComplete="new-password"
          value={password2}
          onChange={(e) => setPassword2(e.target.value)}
          required
        />
        {fieldError("password2") && <p className="field__help" style={{ color: "var(--red)" }}>{fieldError("password2")}</p>}
      </div>

      <button className="btn btn--primary btn--block" type="submit" disabled={pending}>
        {pending ? "Yaratilmoqda..." : "Ro'yxatdan o'tish"}
      </button>
    </form>
  );
}
