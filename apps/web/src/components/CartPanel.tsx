"use client";

import React from "react";
import { ShoppingBag, CheckCircle2, HelpCircle, ArrowRight } from "lucide-react";
import { useI18n } from "../lib/i18n";
import { formatRupiah } from "../lib/currency";
import { CartSnapshot, PendingQuestionEvent, DialogState } from "../types/protocol";

interface CartPanelProps {
  cart: CartSnapshot;
  dialogState: DialogState;
  pendingQuestion: PendingQuestionEvent | null;
  cartUpdatedCue: boolean;
  onSelectPendingChoice?: (choiceId: string) => void;
}

export function CartPanel({
  cart,
  dialogState,
  pendingQuestion,
  cartUpdatedCue,
  onSelectPendingChoice,
}: CartPanelProps) {
  const { t, locale } = useI18n();

  const subtotal = cart.total_price;
  const tax = Math.round(subtotal * 0.1);
  const total = subtotal + tax;

  return (
    <section
      aria-labelledby="cart-heading"
      className="bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-5 flex flex-col h-full shadow-lg"
    >
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <ShoppingBag className="w-4 h-4 text-emerald-400" />
          <h2 id="cart-heading" className="text-sm font-semibold text-white">
            {t.cartTitle}
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {cartUpdatedCue && (
            <span
              role="status"
              className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 animate-bounce motion-reduce:animate-none flex items-center gap-1"
            >
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              {t.cartUpdatedCue}
            </span>
          )}
          <span className="text-xs text-slate-400 font-mono">
            {cart.total_item_count} {t.itemsCount}
          </span>
        </div>
      </div>

      {/* Cart Content with ARIA live region */}
      <div
        role="region"
        tabIndex={0}
        aria-label="Daftar item keranjang / Cart items"
        aria-live="polite"
        className="flex-1 overflow-y-auto space-y-2.5 pr-1 min-h-[160px] max-h-[300px] md:max-h-[360px] focus:outline-none focus:ring-1 focus:ring-emerald-500/50 rounded-xl"
      >
        {cart.items.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500">
            <ShoppingBag className="w-8 h-8 mb-2 stroke-1 text-slate-600" />
            <p className="text-xs max-w-xs">{t.cartEmpty}</p>
          </div>
        ) : (
          cart.items.map((item) => {
            const displayName =
              locale === "en" && item.name_en ? item.name_en : item.name_id || item.item_id;

            return (
              <div
                key={item.line_id || item.item_id}
                className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="w-5 h-5 rounded-md bg-emerald-950 text-emerald-400 font-mono text-xs font-bold flex items-center justify-center shrink-0">
                        {item.quantity}×
                      </span>
                      <h3 className="text-xs font-semibold text-slate-100 truncate">
                        {displayName}
                      </h3>
                      {item.size && item.size !== "regular" && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-slate-800 text-amber-300">
                          {item.size}
                        </span>
                      )}
                    </div>

                    {/* Modifiers and Slot choices */}
                    {(item.modifiers.length > 0 || Object.keys(item.slots || {}).length > 0) && (
                      <div className="mt-1 pl-7 text-[11px] text-slate-400 space-y-0.5">
                        {item.modifiers.map((mod) => (
                          <div key={mod} className="text-slate-400">
                            + {mod.replace(/_/g, " ")}
                          </div>
                        ))}
                        {Object.entries(item.slots || {}).map(([slot, choice]) => (
                          <div key={slot} className="text-sky-300">
                            • {slot}: <span className="font-medium text-sky-200">{choice.replace(/_/g, " ")}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="text-right shrink-0">
                    <span className="text-xs font-mono font-semibold text-emerald-400">
                      {formatRupiah(item.price)}
                    </span>
                    {item.quantity > 1 && item.unit_price && (
                      <span className="block text-[10px] text-slate-500 font-mono">
                        @{formatRupiah(item.unit_price)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Pending Question / Choice Required Banner */}
      {dialogState === "awaiting_choice" && pendingQuestion && (
        <div
          role="alert"
          className="mt-3 p-3 rounded-xl bg-amber-950/40 border border-amber-800/80 text-amber-200"
        >
          <div className="flex items-center gap-1.5 mb-1.5">
            <HelpCircle className="w-4 h-4 text-amber-400 shrink-0" />
            <h4 className="text-xs font-bold text-amber-300">
              {t.pendingChoiceTitle}
            </h4>
          </div>
          <p className="text-xs text-amber-100 mb-2 font-medium">
            {pendingQuestion.prompt}
          </p>

          {pendingQuestion.choices && pendingQuestion.choices.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {pendingQuestion.choices.map((choice) => {
                const choiceLabel =
                  locale === "en" ? choice.name_en : choice.name_id;
                return (
                  <button
                    key={choice.id}
                    type="button"
                    onClick={() => onSelectPendingChoice?.(choice.id)}
                    className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-900/60 hover:bg-amber-800 text-amber-100 border border-amber-700/60 transition flex items-center gap-1"
                  >
                    <span>{choiceLabel}</span>
                    <ArrowRight className="w-3 h-3 text-amber-300" />
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Totals & Price Summary */}
      <div className="pt-3 mt-3 border-t border-slate-800 text-xs space-y-1.5 font-mono">
        <div className="flex justify-between text-slate-400">
          <span>{t.subtotal}:</span>
          <span>{formatRupiah(subtotal)}</span>
        </div>
        <div className="flex justify-between text-slate-400">
          <span>{t.tax}:</span>
          <span>{formatRupiah(tax)}</span>
        </div>
        <div className="flex justify-between text-sm font-bold text-white pt-1.5 border-t border-slate-800/80">
          <span>{t.total}:</span>
          <span className="text-emerald-400">{formatRupiah(total)}</span>
        </div>
      </div>
    </section>
  );
}
