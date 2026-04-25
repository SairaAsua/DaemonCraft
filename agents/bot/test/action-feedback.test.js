import test from 'node:test';
import assert from 'node:assert/strict';
import {
  inventoryHint,
  itemCounts,
  recipeIngredientCounts,
  recipeDiagnostics,
} from '../lib/action_feedback.js';

const fakeMcData = {
  items: {
    5: { name: 'oak_planks' },
    280: { name: 'stick' },
  },
};

test('inventoryHint explains empty inventory', () => {
  assert.equal(inventoryHint([]), 'Inventory is empty.');
});

test('inventoryHint summarizes available items by count', () => {
  const text = inventoryHint([
    { name: 'dirt', count: 2 },
    { name: 'oak_log', count: 1 },
    { name: 'dirt', count: 3 },
  ]);

  assert.equal(text, 'You have: dirt(5), oak_log(1).');
});

test('itemCounts aggregates inventory stacks', () => {
  assert.deepEqual(itemCounts([
    { name: 'oak_planks', count: 2 },
    { name: 'oak_planks', count: 3 },
    { name: 'stick', count: 1 },
  ]), {
    oak_planks: 5,
    stick: 1,
  });
});

test('recipeIngredientCounts reads shaped recipe slots and scales by craft count', () => {
  const recipe = {
    inShape: [
      [5, 5],
      [null, 280],
    ],
  };

  assert.deepEqual(recipeIngredientCounts(recipe, fakeMcData, 2), {
    oak_planks: 4,
    stick: 2,
  });
});

test('recipeDiagnostics reports missing ingredients and table requirement', () => {
  const recipe = {
    requiresTable: true,
    inShape: [[5, 5], [null, 280]],
  };

  const text = recipeDiagnostics(recipe, fakeMcData, { oak_planks: 1 }, 1, false);

  assert.match(text, /needs crafting table nearby/);
  assert.match(text, /missing oak_planks x1/);
  assert.match(text, /stick x1/);
});
