// DEMO PROJECT component for the gfm-skills brag evals.
export function RecipeCard({ recipe }) {
  const missing = recipe.needs.filter((n) => !recipe.have.includes(n));
  return (
    <article className="recipe-card">
      <h3>{recipe.title}</h3>
      <p>Uses {recipe.have.length} of {recipe.needs.length} things you have</p>
      {missing.length === 0 ? <span className="badge-zero">Nothing to buy</span> : <span>Buy: {missing.join(", ")}</span>}
      {recipe.swap && <p className="swap">Missing {recipe.swap.from}? Use {recipe.swap.to}.</p>}
    </article>
  );
}
