"use client";

import React, { useState } from "react";
import { UtensilsCrossed, AlertTriangle, Clock, Sparkles } from "lucide-react";
import { useI18n } from "../lib/i18n";
import { formatRupiah } from "../lib/currency";
import menuData from "../data/menu.json";
import { PublicMenuData, MenuItem, MenuCombo } from "../types/menu";

export function MenuBoard() {
  const { t, locale } = useI18n();
  const menu = menuData as unknown as PublicMenuData;

  const [activeCategory, setActiveCategory] = useState<string>("combo");

  const filteredItems = menu.items.filter((item) => item.category === activeCategory);
  const isComboCategory = activeCategory === "combo";

  return (
    <section
      aria-labelledby="menu-board-heading"
      className="bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-5 flex flex-col shadow-lg"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800 mb-4">
        <div className="flex items-center gap-2">
          <UtensilsCrossed className="w-4 h-4 text-emerald-400" />
          <h2 id="menu-board-heading" className="text-sm font-semibold text-white">
            {t.menuTitle}
          </h2>
        </div>
        <p className="text-xs text-slate-400">{t.menuSubtitle}</p>
      </div>

      {/* Category Tabs */}
      <div
        role="tablist"
        aria-label="Menu Categories"
        className="flex items-center gap-1.5 overflow-x-auto pb-2 mb-4 scrollbar-none"
      >
        {menu.categories.map((cat) => {
          const isActive = activeCategory === cat.id;
          const label = locale === "en" ? cat.name_en : cat.name_id;

          return (
            <button
              key={cat.id}
              role="tab"
              aria-selected={isActive}
              aria-controls={`panel-${cat.id}`}
              id={`tab-${cat.id}`}
              onClick={() => setActiveCategory(cat.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition shrink-0 ${
                isActive
                  ? "bg-emerald-600 text-white font-semibold shadow-md shadow-emerald-950/40"
                  : "bg-slate-950/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Items Grid */}
      <div
        id={`panel-${activeCategory}`}
        role="tabpanel"
        tabIndex={0}
        aria-labelledby={`tab-${activeCategory}`}
        className="grid grid-cols-1 sm:grid-cols-2 gap-3 overflow-y-auto max-h-[380px] pr-1 focus:outline-none focus:ring-1 focus:ring-emerald-500/50 rounded-xl"
      >
        {isComboCategory
          ? menu.combos.map((combo) => renderComboCard(combo, locale, t))
          : filteredItems.map((item) => renderItemCard(item, locale, t))}
      </div>
    </section>
  );
}

function renderItemCard(item: MenuItem, locale: string, t: any) {
  const name = locale === "en" ? item.name_en : item.name_id;
  const isAvailable = item.in_stock && item.available_hours !== "breakfast";

  return (
    <div
      key={item.id}
      className={`p-3 rounded-xl border transition flex flex-col justify-between ${
        isAvailable
          ? "bg-slate-950/60 border-slate-800/80 hover:border-slate-700"
          : "bg-slate-950/30 border-slate-900 opacity-60"
      }`}
    >
      <div>
        <div className="flex items-start justify-between gap-2 mb-1">
          <h3 className="text-xs font-semibold text-slate-100">{name}</h3>
          <span className="text-xs font-mono font-bold text-emerald-400 shrink-0">
            {formatRupiah(item.price)}
          </span>
        </div>

        {/* Availability status badges */}
        <div className="flex flex-wrap gap-1 mt-1.5">
          {!item.in_stock && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-950/80 text-rose-300 border border-rose-800">
              <AlertTriangle className="w-2.5 h-2.5" />
              {t.outOfStock}
            </span>
          )}
          {item.available_hours === "breakfast" && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium bg-amber-950/60 text-amber-300 border border-amber-800/60">
              <Clock className="w-2.5 h-2.5" />
              {t.breakfastOnly}
            </span>
          )}
        </div>
      </div>

      {item.sizes && item.sizes.length > 0 && (
        <div className="mt-2 pt-2 border-t border-slate-900 text-[10px] text-slate-500 font-mono">
          Variants: {item.sizes.map((s) => s.size).join(" / ")}
        </div>
      )}
    </div>
  );
}

function renderComboCard(combo: MenuCombo, locale: string, t: any) {
  const name = locale === "en" ? combo.name_en : combo.name_id;
  const isAvailable = combo.in_stock;

  return (
    <div
      key={combo.id}
      className={`p-3 rounded-xl border transition flex flex-col justify-between ${
        isAvailable
          ? "bg-slate-950/60 border-slate-800/80 hover:border-slate-700"
          : "bg-slate-950/30 border-slate-900 opacity-60"
      }`}
    >
      <div>
        <div className="flex items-start justify-between gap-2 mb-1">
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <h3 className="text-xs font-semibold text-slate-100">{name}</h3>
          </div>
          <span className="text-xs font-mono font-bold text-emerald-400 shrink-0">
            {formatRupiah(combo.base_price)}
          </span>
        </div>

        {/* Slot details */}
        {combo.slots && combo.slots.length > 0 && (
          <div className="mt-1.5 space-y-0.5 text-[11px] text-slate-400">
            {combo.slots.map((s) => (
              <div key={s.slot_id} className="text-slate-400">
                • {locale === "en" ? s.name_en : s.name_id}
              </div>
            ))}
          </div>
        )}

        {/* Out of stock badge */}
        {!combo.in_stock && (
          <span className="inline-flex items-center gap-1 mt-2 px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-950/80 text-rose-300 border border-rose-800">
            <AlertTriangle className="w-2.5 h-2.5" />
            {t.outOfStock}
          </span>
        )}
      </div>
    </div>
  );
}
