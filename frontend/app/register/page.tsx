import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import Icon from "@/components/Icon";
import RegisterForm from "@/components/RegisterForm";

export const metadata: Metadata = { title: "Ro'yxatdan o'tish" };

export default function RegisterPage() {
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
          <h1 className="auth__title">Hisob yarating</h1>
          <p className="auth__subtitle">Bepul ro&apos;yxatdan o&apos;ting — bir necha soniya.</p>

          <RegisterForm />

          <p className="auth__switch">
            Hisobingiz bormi? <Link href="/login/">Kirish</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
