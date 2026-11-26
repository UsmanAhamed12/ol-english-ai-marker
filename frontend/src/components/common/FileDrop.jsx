import { useRef } from "react";
import { FileText, Upload, X } from "lucide-react";

export default function FileDrop({ label, hint, files, onChange, multiple = true, limit = 6 }) {
  const inputRef = useRef(null);

  const add = (list) => {
    const incoming = Array.from(list || []);
    if (!incoming.length) return;
    onChange(multiple ? [...files, ...incoming].slice(0, limit) : [incoming[0]]);
  };

  const removeAt = (index) => {
    onChange(files.filter((_, position) => position !== index));
  };

  return (
    <div>
      <p className="mb-2 text-sm font-medium text-ink">{label}</p>

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          add(event.dataTransfer.files);
        }}
        className="w-full rounded-2xl border-2 border-dashed border-line bg-paper px-5 py-8 text-center transition hover:border-ink/40 hover:bg-paperDeep/60"
      >
        <Upload className="mx-auto h-5 w-5 text-inkSoft" />
        <p className="mt-2 text-sm text-ink">Click to choose files</p>
        <p className="mt-1 text-xs text-inkSoft">{hint}</p>
      </button>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        multiple={multiple}
        className="hidden"
        onChange={(event) => {
          add(event.target.files);
          event.target.value = "";
        }}
      />

      {files.length ? (
        <ul className="mt-3 space-y-1.5">
          {files.map((file, index) => (
            <li
              key={`${file.name}-${index}`}
              className="flex items-center gap-2 rounded-lg border border-line bg-white px-3 py-2 text-xs text-ink"
            >
              <FileText className="h-3.5 w-3.5 shrink-0 text-inkSoft" />
              <span className="min-w-0 flex-1 truncate">{file.name}</span>
              <button
                type="button"
                onClick={() => removeAt(index)}
                className="text-inkSoft transition hover:text-red"
                aria-label={`Remove ${file.name}`}
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}