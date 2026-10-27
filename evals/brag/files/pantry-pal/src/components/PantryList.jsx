// DEMO PROJECT component for the gfm-skills brag evals.
const STAPLES = ["eggs", "rice", "onion", "garlic", "tinned tomatoes", "pasta", "lemon", "milk"];

export function PantryList({ items, onAdd, onToggle }) {
  return (
    <div className="pantry">
      <input placeholder="What's in your cupboard?" onKeyDown={(e) => e.key === "Enter" && onAdd(e.target.value)} />
      <ul className="staples">
        {STAPLES.map((s) => (
          <li key={s} className={items.includes(s) ? "on" : ""} onClick={() => onToggle(s)}>{s}</li>
        ))}
      </ul>
      <button className="cta">Find recipes</button>
    </div>
  );
}
