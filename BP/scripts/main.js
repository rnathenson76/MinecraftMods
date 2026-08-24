// ============================================================
//  EMERALD SWORD  —  the magic armour swap   (Adam's mod)
// ============================================================
//
// The Emerald Sword hits for 20 hearts on its own (that's set with
// "minecraft:damage": 40 in BP/items/emerald_sword.json — 2 damage = 1 heart).
//
// This script does the magic part:
//   - The moment you HOLD the Emerald Sword:
//       * whatever armour you were wearing (and your off-hand item) is set
//         aside, and a full set of Emerald Armour + an Emerald Shield is
//         conjured onto you;
//       * the emerald gear AND the sword in your hand are enchanted with every
//         enchantment they can take, each at its highest level.
//   - The moment you put the sword away (switch to another slot), the conjured
//     emerald gear vanishes and your EXACT old armour goes right back on.
//
// The old armour is remembered on the player (so it survives even a relog) and
// only ever moved back onto you — never copied — so nothing duplicates.

import {
  world,
  system,
  EquipmentSlot,
  ItemStack,
  EnchantmentTypes,
} from "@minecraft/server";

const SWORD = "familymods:emerald_sword";
const PREFIX = "familymods:emerald_";     // marks our conjured gear
const FLAG = "familymods:emeralded";      // per-player "armour is swapped" flag
const SAVED = "familymods:saved_armor";   // per-player stash of the old armour

// Enchantments we deliberately skip: the curses. Curse of Binding would glue
// the emerald armour on and stop us swapping it back; Curse of Vanishing makes
// gear disappear on death. Enchantment ids can come through with or without the
// "minecraft:" namespace, so we compare on the bare name and also catch
// anything that calls itself a curse.
const SKIP_ENCHANTS = new Set(["binding", "vanishing"]);

function isCurse(type) {
  const name = String(type.id).replace(/^minecraft:/, "").toLowerCase();
  return SKIP_ENCHANTS.has(name) || name.includes("curse");
}

// Which slot gets which conjured piece (in slot order).
const CONJURED = [
  ["Head", EquipmentSlot.Head, "familymods:emerald_helmet"],
  ["Chest", EquipmentSlot.Chest, "familymods:emerald_chestplate"],
  ["Legs", EquipmentSlot.Legs, "familymods:emerald_leggings"],
  ["Feet", EquipmentSlot.Feet, "familymods:emerald_boots"],
  ["Offhand", EquipmentSlot.Offhand, "familymods:emerald_shield"],
];

function isHoldingSword(player) {
  const inv = player.getComponent("minecraft:inventory")?.container;
  if (!inv) return false;
  const held = inv.getItem(player.selectedSlotIndex);
  return held?.typeId === SWORD;
}

// Slap every legal enchantment (max level) onto an item, respecting conflicts.
// canAddEnchantment() returns false once a clashing one is already on, so a
// simple greedy pass gives the fullest valid set the item can hold.
function maxEnchant(item) {
  const ench = item?.getComponent("minecraft:enchantable");
  if (!ench) return item;
  for (const type of EnchantmentTypes.getAll()) {
    if (isCurse(type)) continue;
    const entry = { type, level: type.maxLevel };
    try {
      if (ench.canAddEnchantment(entry)) ench.addEnchantment(entry);
    } catch (e) {
      // enchantment not applicable to this item — skip it
    }
  }
  return item;
}

// --- remember / rebuild the player's real gear across the swap ---------------
// We store just enough to rebuild it (id, count, durability, enchantments,
// custom name) as text on the player, so it survives a relog too.
function serializeItem(item) {
  if (!item) return null;
  const data = { id: item.typeId, amount: item.amount };
  const dur = item.getComponent("minecraft:durability");
  if (dur) data.damage = dur.damage;
  const ench = item.getComponent("minecraft:enchantable");
  if (ench) {
    const list = ench.getEnchantments().map((e) => ({ id: e.type.id, lvl: e.level }));
    if (list.length) data.ench = list;
  }
  if (item.nameTag) data.name = item.nameTag;
  return data;
}

function deserializeItem(data) {
  if (!data) return undefined;
  let item;
  try {
    item = new ItemStack(data.id, data.amount ?? 1);
  } catch (e) {
    return undefined; // item no longer exists — nothing to give back
  }
  if (data.name) item.nameTag = data.name;
  const dur = item.getComponent("minecraft:durability");
  if (dur && typeof data.damage === "number") dur.damage = data.damage;
  const ench = item.getComponent("minecraft:enchantable");
  if (ench && data.ench) {
    for (const e of data.ench) {
      const type = EnchantmentTypes.get(e.id);
      if (type) {
        try { ench.addEnchantment({ type, level: e.lvl }); } catch (_) {}
      }
    }
  }
  return item;
}

// If we ever can't put gear back on a slot, drop it in the bags (or at the
// player's feet if full) so nothing is ever lost.
function returnToBags(player, item) {
  if (!item) return;
  const inv = player.getComponent("minecraft:inventory")?.container;
  const leftover = inv ? inv.addItem(item) : item;
  if (leftover) player.dimension.spawnItem(leftover, player.location);
}

function equipEmerald(player) {
  const gear = player.getComponent("minecraft:equippable");
  if (!gear) return;

  const saved = {};
  for (const [name, slot, id] of CONJURED) {
    const current = gear.getEquipment(slot);
    // Remember the real gear (never remember our own conjured pieces).
    saved[name] = current && !current.typeId.startsWith(PREFIX)
      ? serializeItem(current)
      : null;
    gear.setEquipment(slot, maxEnchant(new ItemStack(id, 1)));
  }
  player.setDynamicProperty(SAVED, JSON.stringify(saved));

  // Enchant the sword actually in the player's hand, then write it back.
  const inv = player.getComponent("minecraft:inventory")?.container;
  if (inv) {
    const slotIndex = player.selectedSlotIndex;
    const sword = inv.getItem(slotIndex);
    if (sword?.typeId === SWORD) {
      maxEnchant(sword);
      inv.setItem(slotIndex, sword);
    }
  }

  player.setDynamicProperty(FLAG, true);
}

function removeEmerald(player) {
  const gear = player.getComponent("minecraft:equippable");
  if (!gear) return;

  let saved = {};
  const raw = player.getDynamicProperty(SAVED);
  if (typeof raw === "string") {
    try { saved = JSON.parse(raw); } catch (_) {}
  }

  for (const [name, slot] of CONJURED) {
    const current = gear.getEquipment(slot);
    const old = deserializeItem(saved[name]);
    if (current && current.typeId.startsWith(PREFIX)) {
      // Conjured piece is still there — swap the real gear back in (or clear).
      gear.setEquipment(slot, old);
    } else if (old) {
      // Player changed this slot themselves while holding the sword; don't
      // clobber it — just hand the remembered piece back.
      returnToBags(player, old);
    }
  }

  player.setDynamicProperty(SAVED, undefined);
  player.setDynamicProperty(FLAG, false);
}

// Check a few times a second — responsive without being heavy.
system.runInterval(() => {
  for (const player of world.getAllPlayers()) {
    try {
      const holding = isHoldingSword(player);
      const swapped = player.getDynamicProperty(FLAG) === true;
      if (holding && !swapped) {
        equipEmerald(player);
      } else if (!holding && swapped) {
        removeEmerald(player);
      }
    } catch (e) {
      // player not fully loaded this tick — try again next time
    }
  }
}, 5);
