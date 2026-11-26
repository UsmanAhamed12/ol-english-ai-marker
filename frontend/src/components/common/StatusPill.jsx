const STYLES = {
  draft: { label: "Draft", className: "border-line text-inkSoft bg-white" },
  extracting: { label: "Reading script", className: "border-[#2f5a8f]/30 text-[#2f5a8f] bg-[#eaf1f9]" },
  extracted: { label: "Script read", className: "border-[#2f5a8f]/30 text-[#2f5a8f] bg-[#eaf1f9]" },
  marking: { label: "Marking", className: "border-[#8a6a10]/30 text-[#8a6a10] bg-[#fbf4dc]" },
  marked: { label: "Marked", className: "border-sage/40 text-sage bg-sageWash" },
  review: { label: "Needs review", className: "border-[#8a6a10]/30 text-[#8a6a10] bg-[#fbf4dc]" },
  failed: { label: "Failed", className: "border-red/40 text-red bg-redWash" },
};

export default function StatusPill({ status }) {
  const entry = STYLES[status] || STYLES.draft;
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[0.65rem] font-medium uppercase tracking-wider ${entry.className}`}
    >
      {entry.label}
    </span>
  );
}