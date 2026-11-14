(() => {
  const todayInput = document.getElementById("today");
  const fridgeList = document.getElementById("fridge-list");
  const recipeList = document.getElementById("recipe-list");
  const shoppingList = document.getElementById("shopping-list");
  const addError = document.getElementById("add-error");
  const recipeError = document.getElementById("recipe-error");
  const ingredientList = document.getElementById("ingredient-list");

  function todayValue() {
    return todayInput.value || new Date().toISOString().slice(0, 10);
  }

  function setDefaultToday() {
    if (!todayInput.value) {
      todayInput.value = "2026-11-14";
    }
  }

  async function api(path, options = {}) {
    const response = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.error || `Request failed (${response.status})`);
    }
    return data;
  }

  function showError(el, message) {
    if (!message) {
      el.hidden = true;
      el.textContent = "";
      return;
    }
    el.hidden = false;
    el.textContent = message;
  }

  function colorBadge(color, daysLeft) {
    const label =
      color === "gray" ? "expired" : daysLeft === 0 ? "today" : `${daysLeft}d`;
    const span = document.createElement("span");
    span.className = `badge ${color}`;
    span.textContent = label;
    return span;
  }

  function renderFridge(items) {
    fridgeList.innerHTML = "";
    if (!items.length) {
      const li = document.createElement("li");
      li.textContent = "No provisions yet. Load the sample fridge to demo.";
      fridgeList.appendChild(li);
      return;
    }

    items.forEach((item) => {
      const li = document.createElement("li");
      const meta = document.createElement("div");
      meta.className = "item-meta";
      const name = document.createElement("span");
      name.className = "item-name";
      name.textContent = item.name;
      const expires = document.createElement("span");
      expires.textContent = item.expires_on;
      meta.append(name, expires);

      const actions = document.createElement("div");
      actions.className = "row";
      actions.appendChild(colorBadge(item.color, item.days_left));
      const throwBtn = document.createElement("button");
      throwBtn.className = "danger";
      throwBtn.type = "button";
      throwBtn.textContent = item.color === "gray" ? "Throw out?" : "Throw out";
      throwBtn.addEventListener("click", async () => {
        await api(`/api/items/${item.id}/throw`, {
          method: "POST",
          body: JSON.stringify({ today: todayValue() }),
        });
        await refreshAll();
      });
      actions.appendChild(throwBtn);
      li.append(meta, actions);
      fridgeList.appendChild(li);
    });
  }

  function renderRecipes(recipes, emptyMessage) {
    recipeList.innerHTML = "";
    if (!recipes.length) {
      const p = document.createElement("p");
      p.className = "hint";
      p.textContent = emptyMessage;
      recipeList.appendChild(p);
      return;
    }

    recipes.forEach((recipe) => {
      const card = document.createElement("article");
      card.className = "recipe-card";

      const header = document.createElement("div");
      header.className = "row between";
      const title = document.createElement("h3");
      title.textContent = recipe.name;
      const score = document.createElement("span");
      score.className = "score";
      score.textContent = String(recipe.score);
      header.append(title, score);

      const usesRow = document.createElement("div");
      usesRow.className = "chip-row";
      recipe.uses.forEach((u) => {
        const chip = document.createElement("span");
        chip.className = `chip badge ${u.color}`;
        chip.textContent = `${u.name} · ${u.urgency_points}`;
        usesRow.appendChild(chip);
      });

      const missingRow = document.createElement("div");
      missingRow.className = "chip-row";
      recipe.missing.forEach((m) => {
        const chip = document.createElement("span");
        chip.className = "chip missing";
        chip.textContent = `need: ${m}`;
        missingRow.appendChild(chip);
      });

      const cookBtn = document.createElement("button");
      cookBtn.type = "button";
      cookBtn.textContent = "Cooked it";
      cookBtn.addEventListener("click", async () => {
        await api("/api/cook", {
          method: "POST",
          body: JSON.stringify({
            recipe_name: recipe.name,
            today: todayValue(),
          }),
        });
        await refreshAll();
      });

      card.append(header, usesRow, missingRow, cookBtn);
      recipeList.appendChild(card);
    });
  }

  function renderShopping(items) {
    shoppingList.innerHTML = "";
    if (!items.length) {
      const li = document.createElement("li");
      li.textContent = "Empty — cook a recipe with missing ingredients.";
      shoppingList.appendChild(li);
      return;
    }
    items.forEach((name) => {
      const li = document.createElement("li");
      li.textContent = name;
      shoppingList.appendChild(li);
    });
  }

  function renderStats(data) {
    document.getElementById("saved-count").textContent = data.saved_count;
    document.getElementById("wasted-count").textContent = data.wasted_count;
    document.getElementById("money-saved").textContent = `$${data.estimated_money_saved}`;
  }

  async function refreshAll() {
    const today = todayValue();
    const [fridge, ranked, shop, impact] = await Promise.all([
      api(`/api/items?today=${encodeURIComponent(today)}`),
      api(`/api/rank?today=${encodeURIComponent(today)}`),
      api("/api/shopping-list"),
      api("/api/stats"),
    ]);
    renderFridge(fridge.items);
    renderRecipes(ranked.recipes, "Add food to see ranked recipes.");
    renderShopping(shop.items);
    renderStats(impact);
  }

  async function loadIngredients() {
    const items = await api("/api/ingredients");
    ingredientList.innerHTML = "";
    items.forEach((name) => {
      const option = document.createElement("option");
      option.value = name;
      ingredientList.appendChild(option);
    });
  }

  document.getElementById("add-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    showError(addError, "");
    try {
      await api("/api/items", {
        method: "POST",
        body: JSON.stringify({
          name: document.getElementById("item-name").value,
          expires_on: document.getElementById("item-expires").value,
          today: todayValue(),
        }),
      });
      event.target.reset();
      await refreshAll();
    } catch (err) {
      showError(addError, err.message);
    }
  });

  document.getElementById("sample-btn").addEventListener("click", async () => {
    showError(addError, "");
    await api("/api/sample-fridge", {
      method: "POST",
      body: JSON.stringify({ today: todayValue() }),
    });
    await refreshAll();
  });

  document.getElementById("this-week-btn").addEventListener("click", async () => {
    const data = await api(
      `/api/this-week?today=${encodeURIComponent(todayValue())}`
    );
    renderRecipes(data.plan, "No multi-recipe plan for this fridge.");
  });

  document.getElementById("recipe-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    showError(recipeError, "");
    try {
      const ingredients = document
        .getElementById("recipe-ingredients")
        .value.split(",")
        .map((part) => part.trim())
        .filter(Boolean);
      await api("/api/recipes", {
        method: "POST",
        body: JSON.stringify({
          name: document.getElementById("recipe-name").value,
          ingredients,
        }),
      });
      event.target.reset();
      await refreshAll();
    } catch (err) {
      showError(recipeError, err.message);
    }
  });

  document.getElementById("reload").addEventListener("click", () => refreshAll());
  todayInput.addEventListener("change", () => refreshAll());

  setDefaultToday();
  loadIngredients()
    .then(refreshAll)
    .catch((err) => showError(addError, err.message));
})();
