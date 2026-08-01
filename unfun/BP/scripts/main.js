// ============================================================
//  UNFUN  —  Minecraft, but it starts miserable and you grind
//            four skill bars to earn your game back.
// ============================================================
//
// The joke (recreated from EightSidedSquare's "Unfun" mod): the moment you
// spawn, everything is nerfed — you move slow, you dig slow, you hit like a
// wet noodle. You claw your abilities back by GRINDING four skill bars:
//
//     MINING    — break blocks            -> lifts Mining Fatigue, then Haste
//     BUILDING  — place blocks            -> lifts Slowness,       then Speed
//     CRAFTING  — craft items             -> lifts Weakness,       then Strength
//     SMELTING  — smelt items in furnaces -> Resistance,   then + Regeneration
//
// Each bar fills as you do that activity. Fill it up -> that skill LEVELS UP
// -> its nerf eases and (past a few levels) flips into a real buff. The four
// bars are always shown on screen (the action bar, above the hotbar).
//
// The fun tuning numbers all live in the CONFIG block right below.

import { world, system } from "@minecraft/server";

// ============================================================
//  CONFIG  —  these are the fun ones to experiment with
// ============================================================

const MAX_LEVEL = 15;            // how high each skill can go

// XP you earn per action:
const XP = {
  mineBlock:  4,                 // breaking a normal block
  mineOre:    8,                 // breaking anything ending in "_ore"
  mineSoft:   1,                 // leaves/grass/flowers (cheap to break)
  placeBlock: 3,                 // placing a block
  craft:      5,                 // one detected crafting action
  smeltItem:  5,                 // per item that comes out of a furnace
};

// XP needed to go from `level` to `level+1`  (small early, grows steadily):
function xpToNext(level) { return 40 + level * 40; }

// How the three "nerf -> buff" skills feel at each level.
//  bad  = the punishing effect you start with (eases as you level)
//  good = the reward effect you unlock at higher levels
function nerfToBuffTier(level) {
  if (level <= 1)  return { kind: "bad",  amp: 0 }; // level I nerf
  if (level <= 3)  return { kind: "none" };         // nerf gone, no buff yet
  if (level <= 7)  return { kind: "good", amp: 0 }; // buff I
  if (level <= 11) return { kind: "good", amp: 1 }; // buff II
  return { kind: "good", amp: 2 };                  // buff III
}

// Smelting is the "survival" track — a pure reward, no starting nerf.
function smeltingEffects(level) {
  if (level >= 11) return [["resistance", 1], ["regeneration", 0]];
  if (level >= 7)  return [["resistance", 1]];
  if (level >= 3)  return [["resistance", 0]];
  return [];
}

const EFFECT_DURATION = 60;      // ticks; re-applied every second so it never flickers off
const SEG = 10;                  // segments in each on-screen progress bar
const MAX_FURNACES = 64;         // most furnaces tracked at once
const OUTPUT_SLOT = 2;           // furnace container slot that holds the smelted result

const SKILLS = ["mining", "building", "crafting", "smelting"];
const SKILL_LABEL = {
  mining: "Mining", building: "Building", crafting: "Crafting", smelting: "Smelting",
};
const FURNACE_TYPES = new Set([
  "minecraft:furnace", "minecraft:lit_furnace",
  "minecraft:blast_furnace", "minecraft:lit_blast_furnace",
  "minecraft:smoker", "minecraft:lit_smoker",
]);

// ============================================================
//  SKILL STORAGE  —  saved per player, survives relog/rejoin
// ============================================================

function num(player, key, dflt) {
  const v = player.getDynamicProperty(key);
  return typeof v === "number" ? v : dflt;
}
function getLvl(player, skill) { return num(player, `unfun:${skill}_lvl`, 0); }
function getXp(player, skill)  { return num(player, `unfun:${skill}_xp`, 0); }

function addXp(player, skill, amount) {
  if (!player || amount <= 0) return;
  let lvl = getLvl(player, skill);
  if (lvl >= MAX_LEVEL) return;

  let xp = getXp(player, skill) + amount;
  let need = xpToNext(lvl);
  let leveled = false;
  while (xp >= need && lvl < MAX_LEVEL) {
    xp -= need;
    lvl++;
    leveled = true;
    need = xpToNext(lvl);
  }
  if (lvl >= MAX_LEVEL) xp = 0;

  player.setDynamicProperty(`unfun:${skill}_lvl`, lvl);
  player.setDynamicProperty(`unfun:${skill}_xp`, xp);

  if (leveled) {
    const capped = lvl >= MAX_LEVEL ? " §b(MAX)" : "";
    player.sendMessage(`§6${SKILL_LABEL[skill]} leveled up! §fLv ${lvl}${capped}§r`);
    try { player.playSound("random.levelup"); } catch (e) { /* sound is optional */ }
  }
}

function resetPlayer(player) {
  for (const s of SKILLS) {
    player.setDynamicProperty(`unfun:${s}_lvl`, 0);
    player.setDynamicProperty(`unfun:${s}_xp`, 0);
  }
}

// ============================================================
//  MINING  —  break a block  (rock-solid vanilla event)
// ============================================================

world.afterEvents.playerBreakBlock.subscribe((e) => {
  const id = e.brokenBlockPermutation?.type?.id ?? "";
  let gain = XP.mineBlock;
  if (id.endsWith("_ore") || id.includes("ancient_debris")) gain = XP.mineOre;
  else if (/leaves|grass|flower|sapling|wool|carpet|snow_layer|vine|fern|tallgrass/.test(id)) gain = XP.mineSoft;
  addXp(e.player, "mining", gain);
  markPhysical(e.player);
});

// ============================================================
//  BUILDING  —  place a block  (rock-solid vanilla event)
// ============================================================

world.afterEvents.playerPlaceBlock.subscribe((e) => {
  addXp(e.player, "building", XP.placeBlock);
  markPhysical(e.player);
});

// ============================================================
//  CRAFTING  —  Bedrock has no "craft" event, so we watch the
//  inventory: a craft consumes ingredients AND produces a new
//  item in the same instant. If, since the last check, some item
//  count went DOWN while another went UP, that's a craft.
//
//  To avoid mistaking "mined a drop + placed a block" for a
//  craft, we skip the check for a moment after mining/placing.
// ============================================================

const lastPhysicalTick = new Map(); // playerId -> tick of last break/place
const PHYSICAL_COOLDOWN = 12;       // ticks to wait after mining/placing
const invSnapshot = new Map();      // playerId -> Map(typeId -> amount)

function markPhysical(player) { lastPhysicalTick.set(player.id, system.currentTick); }

function inventoryCounts(player) {
  const counts = new Map();
  const container = player.getComponent("minecraft:inventory")?.container;
  if (!container) return counts;
  for (let i = 0; i < container.size; i++) {
    const item = container.getItem(i);
    if (item) counts.set(item.typeId, (counts.get(item.typeId) || 0) + item.amount);
  }
  return counts;
}

system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    const current = inventoryCounts(player);
    const previous = invSnapshot.get(player.id);
    invSnapshot.set(player.id, current);
    if (!previous) continue;

    // Just mined or built? The drop/placement skews the diff — sit this one out.
    const since = system.currentTick - (lastPhysicalTick.get(player.id) ?? -9999);
    if (since < PHYSICAL_COOLDOWN) continue;

    let gained = false, lost = false;
    for (const [id, amt] of current) if (amt > (previous.get(id) || 0)) { gained = true; break; }
    for (const [id, amt] of previous) if ((current.get(id) || 0) < amt) { lost = true; break; }

    if (gained && lost) addXp(player, "crafting", XP.craft); // ingredients out, product in = a craft
  }
}, 10);

// ============================================================
//  SMELTING  —  also no event, so we track the furnaces a player
//  opens and watch their OUTPUT slot. When the result count goes
//  up, that many items just finished smelting -> award the player
//  who last used that furnace.
// ============================================================

const furnaces = new Map(); // key "dim:x,y,z" -> {dim, x, y, z, playerId, lastOut}

function readOutput(dim, x, y, z) {
  try {
    const block = dim.getBlock({ x, y, z });
    if (!block || !FURNACE_TYPES.has(block.typeId)) return null; // furnace gone/changed
    const container = block.getComponent("minecraft:inventory")?.container;
    if (!container) return 0;
    const item = container.getItem(OUTPUT_SLOT);
    return item ? item.amount : 0;
  } catch (e) {
    return null;
  }
}

world.afterEvents.playerInteractWithBlock.subscribe((e) => {
  const block = e.block;
  if (!block || !FURNACE_TYPES.has(block.typeId)) return;

  const x = Math.floor(block.location.x), y = Math.floor(block.location.y), z = Math.floor(block.location.z);
  const key = `${block.dimension.id}:${x},${y},${z}`;
  const existing = furnaces.get(key);
  if (existing) { existing.playerId = e.player.id; return; } // remember the newest user

  if (furnaces.size >= MAX_FURNACES) furnaces.delete(furnaces.keys().next().value); // drop oldest
  const out = readOutput(block.dimension, x, y, z);
  furnaces.set(key, { dim: block.dimension, x, y, z, playerId: e.player.id, lastOut: out ?? 0 });
});

system.runInterval(() => {
  for (const [key, f] of furnaces) {
    const out = readOutput(f.dim, f.x, f.y, f.z);
    if (out === null) { furnaces.delete(key); continue; }
    if (out > f.lastOut) {
      const player = world.getAllPlayers().find((p) => p.id === f.playerId);
      if (player) addXp(player, "smelting", (out - f.lastOut) * XP.smeltItem);
    }
    f.lastOut = out; // also resets when the player collects the result
  }
}, 20);

// ============================================================
//  EFFECTS + ON-SCREEN BARS  —  once a second, per player
// ============================================================

function applyEffect(player, id, amp) {
  try { player.addEffect(id, EFFECT_DURATION, { amplifier: amp, showParticles: false }); } catch (e) { /* ignore */ }
}

function applyNerfToBuff(player, skill, badId, goodId) {
  const t = nerfToBuffTier(getLvl(player, skill));
  if (t.kind === "bad") applyEffect(player, badId, t.amp);
  else if (t.kind === "good") applyEffect(player, goodId, t.amp);
}

function progressBar(player, skill) {
  const lvl = getLvl(player, skill);
  if (lvl >= MAX_LEVEL) return `§7L${lvl} §b§lMAX`;
  const need = xpToNext(lvl);
  const xp = getXp(player, skill);
  const filled = Math.max(0, Math.min(SEG, Math.round((xp / need) * SEG)));
  const bar = `§8[§a${"|".repeat(filled)}§7${"-".repeat(SEG - filled)}§8]`;
  return `§7L§f${lvl} ${bar} §7${xp}/${need}`;
}

system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    // stats
    applyNerfToBuff(player, "mining", "mining_fatigue", "haste");
    applyNerfToBuff(player, "building", "slowness", "speed");
    applyNerfToBuff(player, "crafting", "weakness", "strength");
    for (const [id, amp] of smeltingEffects(getLvl(player, "smelting"))) applyEffect(player, id, amp);

    // bars (action bar, above the hotbar)
    try {
      player.onScreenDisplay.setActionBar(
        [
          "§b§lUNFUN§r §7— earn your game back",
          `§eMining   ${progressBar(player, "mining")}`,
          `§aBuilding ${progressBar(player, "building")}`,
          `§dCrafting ${progressBar(player, "crafting")}`,
          `§6Smelting ${progressBar(player, "smelting")}`,
        ].join("\n")
      );
    } catch (e) { /* screen not ready */ }
  }
}, 20);

// ============================================================
//  WELCOME + CHAT COMMANDS
// ============================================================

world.afterEvents.playerSpawn.subscribe((e) => {
  if (!e.initialSpawn) return;
  const p = e.player;
  for (const s of SKILLS) {
    if (p.getDynamicProperty(`unfun:${s}_lvl`) === undefined) {
      p.setDynamicProperty(`unfun:${s}_lvl`, 0);
      p.setDynamicProperty(`unfun:${s}_xp`, 0);
    }
  }
  p.sendMessage("§b§lUNFUN§r §7activated — everything's nerfed. Mine, build, craft & smelt to earn it back!");
});

// Type these in chat.  (before-event: cancel the message, then act next tick)
world.beforeEvents.chatSend.subscribe((e) => {
  const msg = e.message.trim().toLowerCase();
  const player = e.sender;
  if (msg === "!unfun reset") {
    e.cancel = true;
    system.run(() => { resetPlayer(player); player.sendMessage("§cUnfun progress reset to zero."); });
  } else if (msg === "!unfun max") {
    e.cancel = true;
    system.run(() => {
      for (const s of SKILLS) { player.setDynamicProperty(`unfun:${s}_lvl`, MAX_LEVEL); player.setDynamicProperty(`unfun:${s}_xp`, 0); }
      player.sendMessage("§aUnfun: all skills maxed.");
    });
  } else if (msg === "!unfun help") {
    e.cancel = true;
    system.run(() => player.sendMessage(
      "§bUnfun commands:§r  §f!unfun reset§7 (start over),  §f!unfun max§7 (max all skills for testing)"
    ));
  }
});
