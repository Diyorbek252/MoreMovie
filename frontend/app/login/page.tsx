import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { Suspense } from "react";

import Icon from "@/components/Icon";
import LoginForm from "@/components/LoginForm";

export const metadata: Metadata = { title: "Kirish" };

export default function LoginPage() {
  return (
    <div className="auth">
      <aside className="auth__aside">
        <Image src="/img/logo.svg" alt="MORE-MOVIE" width={220} height={60} />
        <p className="auth__tagline">Cheksiz kino zavqi...</p>
        <ul className="auth__points">
          <li>
            <Icon name="check" /> Watchlist va sevimlilar ro&apos;yxati
          </li>
          <li>
            <Icon name="check" /> To&apos;xtagan joyingizdan davom ettirish
          </li>
          <li>
            <Icon name="check" /> Reyting va sharh qoldirish
          </li>
          <li>
            <Icon name="check" /> Faqat qonuniy, litsenziyalangan kontent
          </li>
        </ul>
      </aside>

      <div className="auth__main">
        <div className="auth__form">
          <h1 className="auth__title">Xush kelibsiz</h1>
          <p className="auth__subtitle">Hisobingizga kiring va tomoshani davom ettiring.</p>

          <Suspense>
            <LoginForm />
          </Suspense>

          <p className="auth__switch">
            Hisobingiz yo&apos;qmi? <Link href="/register/">Ro&apos;yxatdan o&apos;ting</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
