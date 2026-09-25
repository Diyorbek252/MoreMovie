/**
 * Backend serializerlariga aynan mos TypeScript turlari.
 *
 * Manba: movies/serializers.py, series/serializers.py, reviews/serializers.py,
 * users/serializers.py, shop/serializers.py, subscriptions/serializers.py,
 * siteconfig/serializers.py. Bu yerdagi maydon nomlari ular bilan bir xil
 * bo'lishi SHART — mos kelmasa runtime'da jim-jim `undefined` chiqadi
 * (TypeScript buni compile paytida ko'rmaydi, chunki API javobi `any`dan
 * kelib turlarga majburiy moslashtiriladi).
 */

export interface Genre {
  id: number;
  name: string;
  slug: string;
  icon: string;
}

export interface Director {
  id: number;
  full_name: string;
  slug: string;
  photo: string | null;
}

export interface Actor {
  id: number;
  full_name: string;
  slug: string;
  photo: string | null;
}

export interface CastMember {
  actor: Actor;
  character_name: string;
  order: number;
}

export interface Screenshot {
  id: number;
  image: string;
  caption: string;
  order: number;
}

export interface VideoSource {
  quality: string;
  label: string;
  url: string;
}

/** `MovieCardSerializer` — ro'yxat/karta ko'rinishi. */
export interface MovieCard {
  id: number;
  kind: "movie" | "cartoon";
  title: string;
  slug: string;
  poster: string | null;
  backdrop: string | null;
  short_description: string;
  release_year: number;
  duration_display: string;
  quality_badges: string[];
  imdb_rating: string;
  user_rating_display: number | null;
  is_premiere: boolean;
  premiere_label: string;
  is_upcoming_premiere: boolean;
  premiere_date: string | null;
  is_featured: boolean;
  is_trending: boolean;
  is_premium: boolean;
  can_watch: boolean;
  genres: Genre[];
  in_watchlist: boolean;
  in_favorite: boolean;
}

/** `MovieDetailSerializer` — `MovieCard` ning barcha maydonlari + qo'shimchalar. */
export interface MovieDetail extends MovieCard {
  original_title: string;
  description: string;
  meta_description_text: string;
  directors: Director[];
  countries: string[];
  language: string | null;
  age_rating: string;
  best_quality_display: string;
  can_play: boolean;
  video_sources: VideoSource[];
  can_download: boolean;
  download_url: string | null;
  resume_at: number;
  user_rating: number;
  views_count: number;
  cast: CastMember[];
  screenshots: Screenshot[];
  similar_movies: MovieCard[];
  trailer_url: string;
  license_type: "public_domain" | "licensed" | "trailer_only";
  license_type_display: string;
  license_note: string;
}

/** `SeriesCardSerializer`. */
export interface SeriesCard {
  id: number;
  title: string;
  slug: string;
  poster: string | null;
  backdrop: string | null;
  short_description: string;
  release_year: number;
  end_year: number | null;
  status: "announced" | "ongoing" | "completed";
  imdb_rating: string;
  user_rating_display: number | null;
  is_featured: boolean;
  is_trending: boolean;
  is_premium: boolean;
  genres: Genre[];
  season_count: number;
  episode_count: number;
}

export interface Episode {
  id: number;
  episode_number: number;
  title: string;
  description: string;
  display_thumbnail_url: string;
  duration_display: string;
  air_date: string | null;
  views_count: number;
  can_watch: boolean;
  can_play: boolean;
  video_source: string;
  download_url: string | null;
}

export interface Season {
  id: number;
  number: number;
  display_title: string;
  poster: string | null;
  year: number | null;
  episodes: Episode[];
}

export interface SeriesDetail extends SeriesCard {
  original_title: string;
  description: string;
  directors: Director[];
  countries: string[];
  language: string | null;
  age_rating: string;
  cast: CastMember[];
  seasons: Season[];
  similar_series: SeriesCard[];
  views_count: number;
  trailer_url: string;
}

/** Katalog elementi — `kind` orqali Movie/Series ajratiladi (core/api_v1.py::CatalogAPIView). */
export type CatalogItem = ({ kind: "movie" | "cartoon" } & MovieCard) | ({ kind: "series" } & SeriesCard);

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface CatalogResponse extends Paginated<CatalogItem> {
  current: {
    type: string;
    q: string;
    genre: string[];
    year: string[];
    country: string;
    language: string;
    rating: string;
    sort: string;
  };
  type_label: string;
}

export interface HomeSection {
  key: string;
  title: string;
  subtitle: string;
  link: string;
  is_series: boolean;
  items: (MovieCard | SeriesCard | Genre | number)[];
}

export interface ContinueWatchingItem extends MovieCard {
  resume_seconds: number;
  progress_percent: number;
}

export interface HomeResponse {
  hero: MovieCard | null;
  rail_sections: HomeSection[];
  continue_watching: ContinueWatchingItem[];
}

export interface Profile {
  avatar_url: string | null;
  bio: string;
  country: string;
  show_continue_watching: boolean;
  balance: number;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  display_name: string;
  initials: string;
  is_staff: boolean;
  profile: Profile;
}

export interface Review {
  id: number;
  user: { username: string; display_name: string; avatar_url: string | null };
  comment: string;
  user_score: number | null;
  created_at: string;
}

export interface SiteSettings {
  site_name: string;
  logo: string | null;
  favicon: string | null;
  site_description: string;
  contact_email: string;
  telegram: string;
  youtube: string;
  instagram: string;
  facebook: string;
  copyright_text: string;
  seo_title: string;
  seo_description: string;
  seo_keywords: string;
  google_analytics_id: string;
  maintenance_mode: boolean;
  maintenance_message: string;
  payment_card_number: string;
  payment_card_holder: string;
  payment_instructions: string;
}

export interface Banner {
  id: number;
  title: string;
  image: string;
  link: string;
  position: string;
}

export interface Notification {
  id: number;
  title: string;
  message: string;
  type: string;
  link: string;
  image: string;
  is_read: boolean;
  created_at: string;
}

export interface Product {
  id: number;
  name: string;
  slug: string;
  description: string;
  image: string | null;
  price: number;
  stock: number | null;
  is_in_stock: boolean;
}

export interface Order {
  id: number;
  product_name: string;
  quantity: number;
  price_paid: number;
  status: "pending" | "delivered" | "cancelled";
  created_at: string;
  delivered_at: string | null;
}

export interface PlanPrice {
  id: number;
  label: string;
  duration_days: number;
  price: number;
  old_price: number | null;
  monthly_equivalent: number;
  discount_percent: number;
}

export interface Plan {
  id: number;
  name: string;
  slug: string;
  tagline: string;
  description: string;
  feature_list: string[];
  level: number;
  allows_premium_movies: boolean;
  has_badge: boolean;
  is_ad_free: boolean;
  is_highlighted: boolean;
  prices: PlanPrice[];
  cheapest_price: PlanPrice | null;
}

export interface Subscription {
  id: number;
  plan_name: string;
  duration_days: number;
  price_paid: number;
  status: "pending" | "active" | "rejected" | "expired" | "cancelled";
  payment_note: string;
  admin_note: string;
  starts_at: string | null;
  ends_at: string | null;
  is_currently_active: boolean;
  days_left: number;
  percent_left: number;
  created_at: string;
}

/** DRF standart xato shakli: {"field": ["xabar"], "non_field_errors": [...]} yoki {"detail": "..."}. */
export type ApiErrorPayload = Record<string, string[] | string> & { detail?: string };
