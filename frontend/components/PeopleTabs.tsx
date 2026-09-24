"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

import type { CastMember, Director } from "@/lib/types";
import Icon from "./Icon";

export default function PeopleTabs({ cast, directors }: { cast: CastMember[]; directors: Director[] }) {
  const [tab, setTab] = useState<"cast" | "director">("cast");

  return (
    <section className="section">
      <div className="section__head">
        <div className="people-tabs">
          <button
            type="button"
            className={`people-tabs__btn${tab === "cast" ? " is-active" : ""}`}
            onClick={() => setTab("cast")}
          >
            <Icon name="users" /> Aktyorlar
          </button>
          <button
            type="button"
            className={`people-tabs__btn${tab === "director" ? " is-active" : ""}`}
            onClick={() => setTab("director")}
          >
            <Icon name="film" /> Rejissyor
          </button>
        </div>
      </div>

      <div className="cast-rail" hidden={tab !== "cast"}>
        {cast.map((member) => (
          <Link className="cast-card" href={`/actor/${member.actor.slug}/`} key={member.actor.id}>
            {member.actor.photo ? (
              <Image className="cast-card__photo" src={member.actor.photo} alt={member.actor.full_name} width={132} height={132} />
            ) : (
              <div className="cast-card__photo cast-card__photo--initials">
                {member.actor.full_name.slice(0, 2).toUpperCase()}
              </div>
            )}
            <div className="cast-card__name">{member.actor.full_name}</div>
            {member.character_name && <div className="cast-card__role">{member.character_name}</div>}
          </Link>
        ))}
      </div>

      <div className="cast-rail" hidden={tab !== "director"}>
        {directors.map((director) => (
          <Link className="cast-card" href={`/director/${director.slug}/`} key={director.id}>
            {director.photo ? (
              <Image className="cast-card__photo" src={director.photo} alt={director.full_name} width={132} height={132} />
            ) : (
              <div className="cast-card__photo cast-card__photo--initials">
                {director.full_name.slice(0, 2).toUpperCase()}
              </div>
            )}
            <div className="cast-card__name">{director.full_name}</div>
            <div className="cast-card__role">Rejissyor</div>
          </Link>
        ))}
      </div>
    </section>
  );
}
