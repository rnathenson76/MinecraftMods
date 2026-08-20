// ============================================================
//  EMERALD SWORD  —  the magic armour swap   (Adam's mod)
// ============================================================
//
// The Emerald Sword hits for 20 hearts on its own (that's set with
// "minecraft:damage": 40 in BP/items/emerald_sword.json — 2 damage = 1 heart).
//
// This script does the magic part:
//   - The moment you HOLD the Emerald Sword, whatever armour you were wearing
//     is popped off into your inventory and a full set of Emerald Armour +
//     an Emerald Shield is conjured onto you.
//   - The moment you put the sword away (switch to another slot), the conjured
//     emerald gear vanishes again. Your old armour is still sitting in your
//     inventory, ready to put back on.
//
// The old armour is only ever MOVED to your bags — never copied — so nothing
// duplicates. The emerald gear is summoned fresh and removed, so it never
// piles up either.

import { world, system, EquipmentSlot, ItemStack } from "@minecraft/server";

const SWORD = "familymods:emerald_sword";
const PREFIX = "familymods:emerald_";     // marks our conjured gear
const FLAG = "familymods:emeralded";      // per-player "armour is swapped" flag

// Which slot gets which conjured piece.
const CONJURED = [
  [EquipmentSlot.Head, "familymods:emerald_helmet"],
  [EquipmentSlot.Chest, "familymods:emerald_chestplate"],
  [EquipmentSlot.Legs, "familymods:emerald_leggings"],
  [EquipmentSlot.Feet, "familymods:emerald_boots"],
  [EquipmentSlot.Offhand, "familymods:emerald_shield"],
];

function isHoldingSword(player) {
  const inv = player.getComponent("minecraft:inventory")?.container;
  if (!inv) return false;
  const held = inv.getItem(player.selectedSlotIndex);
  return held?.typeId === SWORD;
}

// Put an item back in the player's bags; if they're full, drop it at their feet
// so it's never lost.
function returnToBags(player, item) {
  const inv = player.getComponent("minecraft:inventory")?.container;
  const leftover = inv ? inv.addItem(item) : item;
  if (leftover) {
    player.dimension.spawnItem(leftover, player.location);
  }
}

function equipEmerald(player) {
  const gear = player.getComponent("minecraft:equippable");
  if (!gear) return;
  for (const [slot, id] of CONJURED) {
    const current = gear.getEquipment(slot);
    // Stow the player's real gear (but never our own conjured pieces).
    if (current && !current.typeId.startsWith(PREFIX)) {
      returnToBags(player, current);
    }
    gear.setEquipment(slot, new ItemStack(id, 1));
  }
  player.setDynamicProperty(FLAG, true);
}

function removeEmerald(player) {
  const gear = player.getComponent("minecraft:equippable");
  if (!gear) return;
  for (const [slot] of CONJURED) {
    const current = gear.getEquipment(slot);
    // Only clear our conjured emerald pieces — leave anything the player
    // re-equipped themselves alone.
    if (current && current.typeId.startsWith(PREFIX)) {
      gear.setEquipment(slot, undefined);
    }
  }
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
