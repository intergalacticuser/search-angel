"use client";

import type { SearchCategory } from "@/lib/types";

const CATEGORIES: { value: SearchCategory; label: string; icon: string }[] = [
  { value: "general", label: "Web", icon: "\uD83C\uDF10" },
  { value: "images", label: "Images", icon: "\uD83D\uDDBC\uFE0F" },
  { value: "videos", label: "Videos", icon: "\uD83C\uDFA5" },
  { value: "news", label: "News", icon: "\uD83D\uDCF0" },
  { value: "science", label: "Science", icon: "\uD83D\uDD2C" },
  { value: "books", label: "Books", icon: "\uD83D\uDCDA" },
  { value: "music", label: "Music", icon: "\uD83C\uDFB5" },
  { value: "files", label: "Files", icon: "\uD83D\uDCC1" },
];

interface CategoryTabsProps {
  active: SearchCategory;
  onChange: (category: SearchCategory) => void;
}

export default function CategoryTabs({ active, onChange }: CategoryTabsProps) {
  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-1 scrollbar-none">
      {CATEGORIES.map((cat) => (
        <button
          key={cat.value}
          onClick={() => onChange(cat.value)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm whitespace-nowrap transition-all ${
            active === cat.value
              ? "bg-angel-accent/15 text-angel-accent border border-angel-accent/30"
              : "text-angel-muted hover:text-angel-text hover:bg-angel-surface border border-transparent"
          }`}
        >
          <span className="text-base">{cat.icon}</span>
          {cat.label}
        </button>
      ))}
    </div>
  );
}
