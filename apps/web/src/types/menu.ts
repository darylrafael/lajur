export interface MenuItemSize {
  size: "regular" | "medium" | "large";
  price_delta: number;
}

export interface MenuItemModifierOption {
  id: string;
  name_id: string;
  name_en: string;
  price_delta: number;
}

export interface MenuItemModifier {
  id: string;
  name_id: string;
  name_en: string;
  applies_to: string[];
  required: boolean;
  max: number;
  options: MenuItemModifierOption[];
}

export interface ComboSlot {
  slot_id: string;
  name_id: string;
  name_en: string;
  required: boolean;
  choice_items: string[];
}

export interface MenuItem {
  id: string;
  category: "burger" | "ayam" | "side" | "minuman" | "sarapan" | "dessert";
  name_id: string;
  name_en: string;
  price: number;
  sizes: MenuItemSize[];
  modifiers: string[];
  available_hours: "all_day" | "breakfast" | "regular";
  in_stock: boolean;
}

export interface MenuCombo {
  id: string;
  category: "combo";
  name_id: string;
  name_en: string;
  base_price: number;
  slots: ComboSlot[];
  upsell_rules: Array<{
    rule_id: string;
    prompt_id: string;
    prompt_en: string;
    target_item: string;
    price_delta: number;
  }>;
  available_hours: "all_day" | "breakfast" | "regular";
  in_stock: boolean;
}

export interface MenuCategory {
  id: string;
  name_id: string;
  name_en: string;
}

export interface PublicMenuData {
  version: string;
  currency: string;
  operating_hours: {
    breakfast: { start: string; end: string };
    regular: { start: string; end: string };
  };
  categories: MenuCategory[];
  items: MenuItem[];
  combos: MenuCombo[];
  modifiers: MenuItemModifier[];
}
