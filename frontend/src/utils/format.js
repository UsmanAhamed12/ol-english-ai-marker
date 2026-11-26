export const fmt = (value) => {
  const number = Number(value ?? 0);
  return Number.isInteger(number) ? String(number) : number.toFixed(1);
};

export const formatDate = (value) => {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
};