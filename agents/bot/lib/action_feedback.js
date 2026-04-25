// Pure helpers for action/tool feedback. Keep these side-effect free so tests can
// verify the exact messages agents see after failed actions.

export function itemCounts(items = []) {
  const counts = {};
  for (const item of items) {
    if (!item?.name) continue;
    counts[item.name] = (counts[item.name] || 0) + (item.count || 1);
  }
  return counts;
}

export function inventoryHint(items = [], limit = 8) {
  const counts = itemCounts(items);
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  if (entries.length === 0) return 'Inventory is empty.';
  const have = entries
    .slice(0, limit)
    .map(([name, count]) => `${name}(${count})`)
    .join(', ');
  return `You have: ${have}.`;
}

function slotToNameAndCount(slot, mcData) {
  if (!slot || slot === -1) return null;

  if (typeof slot === 'number') {
    const name = mcData?.items?.[slot]?.name || mcData?.blocks?.[slot]?.name || `id:${slot}`;
    return { name, count: 1 };
  }

  const id = slot.id ?? slot.type;
  if (id == null || id === -1) return null;
  const name = mcData?.items?.[id]?.name || mcData?.blocks?.[id]?.name || `id:${id}`;
  return { name, count: slot.count || 1 };
}

export function recipeIngredientCounts(recipe, mcData, craftCount = 1) {
  const counts = {};
  const slots = recipe?.inShape
    ? recipe.inShape.flat()
    : recipe?.ingredients?.flat?.() || recipe?.ingredients || [];

  for (const slot of slots) {
    const ingredient = slotToNameAndCount(slot, mcData);
    if (!ingredient) continue;
    counts[ingredient.name] = (counts[ingredient.name] || 0) + ingredient.count * craftCount;
  }

  return counts;
}

export function recipeDiagnostics(recipe, mcData, availableCounts, craftCount = 1, hasCraftingTable = false) {
  const required = recipeIngredientCounts(recipe, mcData, craftCount);
  const missing = Object.entries(required)
    .map(([name, requiredCount]) => [name, requiredCount - (availableCounts[name] || 0)])
    .filter(([, missingCount]) => missingCount > 0)
    .map(([name, missingCount]) => `${name} x${missingCount}`);

  const parts = [];
  if (recipe?.requiresTable !== false && !hasCraftingTable) {
    parts.push('needs crafting table nearby');
  }
  if (missing.length > 0) {
    parts.push(`missing ${missing.join(', ')}`);
  }
  if (parts.length === 0) return 'recipe appears craftable; try again near a crafting table if it still fails';
  return parts.join('; ');
}
