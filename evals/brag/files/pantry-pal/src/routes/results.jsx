// DEMO PROJECT route for the gfm-skills brag evals: the screen after "Find recipes".
import { RecipeCard } from "../components/RecipeCard";

const SAMPLE = [
  { title: "Shakshuka", needs: ["eggs", "tinned tomatoes", "onion", "garlic"], have: ["eggs", "tinned tomatoes", "onion", "garlic"] },
  { title: "Lemon garlic pasta", needs: ["pasta", "lemon", "garlic", "parmesan"], have: ["pasta", "lemon", "garlic", "parmesan"] },
  { title: "Egg fried rice", needs: ["rice", "eggs", "onion", "soy sauce"], have: ["rice", "eggs", "onion", "soy sauce"],
    swap: { from: "spring onion", to: "onion" } },
];

export default function Results() {
  return (
    <main>
      <p className="signed-in">Signed in as jo.demo-user@gmail.com</p>
      <h2>3 dinners, 0 trips to the shop</h2>
      {SAMPLE.map((r) => <RecipeCard key={r.title} recipe={r} />)}
    </main>
  );
}
