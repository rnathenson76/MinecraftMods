// ============================================================
//  CARRIER  —  phase 1: the Water Blaster   (Adam's mod)
// ============================================================
//
// The Water Blaster is a water gun:
//   - USE it (tap / right-click)   -> fires a water shot
//   - water shots HURT mobs, knock them back and splash
//   - they put out fire: a burning mob stops burning, and fire blocks
//     next to where the shot lands go out
//   - blazes and endermen hate water, so they take extra damage
//   - the durability bar is the WATER TANK. Every shot uses a bit.
//     Run dry -> look at some water up close and USE it to refill.
//
// How hard a shot hits is "damage" in BP/entities/water_shot.json.
// The rest of the feel is in the numbers right below.

import { world, system } from "@minecraft/server";

const BLASTER = "carrier:water_blaster";
const SHOT = "carrier:water_shot";

// ---- Feel (tweak these!) ----
const SHOT_SPEED = 2.2;       // how fast a shot flies (blocks per tick)
const SHOT_SPREAD = 0.03;     // a little wobble so it sprays, not lasers
const FIRE_DELAY = 4;         // ticks between shots (20 ticks = 1 second)
const REFILL_REACH = 6;       // how close the water has to be to refill
const PUT_OUT_RADIUS = 1;     // fire blocks this close to a splash go out
const WATER_HATER_BONUS = 6;  // extra damage for mobs that hate water
const WATER_HATERS = new Set([
  "minecraft:blaze",
  "minecraft:enderman",
  "minecraft:snow_golem",
]);
const FIRE_BLOCKS = new Set(["minecraft:fire", "minecraft:soul_fire"]);
const WATER_BLOCKS = new Set(["minecraft:water", "minecraft:flowing_water"]);

// A shot vanishes the moment it hits, so its typeId is read carefully.
function isShot(projectile) {
  try {
    return projectile?.typeId === SHOT;
  } catch (e) {
    return false;
  }
}

// remembers, per player, the tick they last fired (so it can't machine-gun)
const lastShot = new Map();

function splash(dimension, location) {
  try {
    for (let i = 0; i < 6; i++) {
      dimension.spawnParticle("minecraft:water_splash_particle", {
        x: location.x + (Math.random() - 0.5) * 0.8,
        y: location.y + Math.random() * 0.6,
        z: location.z + (Math.random() - 0.5) * 0.8,
      });
    }
    dimension.playSound("random.splash", location, { volume: 0.6, pitch: 1.4 });
  } catch (e) { /* chunk not loaded */ }
}

// Looking at water close by? Returns true if it is.
function lookingAtWater(player) {
  try {
    const hit = player.getBlockFromViewDirection({
      includeLiquidBlocks: true,
      includePassableBlocks: true,
      maxDistance: REFILL_REACH,
    });
    return hit !== undefined && WATER_BLOCKS.has(hit.block.typeId);
  } catch (e) {
    return false;
  }
}

function fire(player) {
  const dir = player.getViewDirection();
  const head = player.getHeadLocation();
  const start = { x: head.x + dir.x * 0.8, y: head.y + dir.y * 0.8 - 0.1, z: head.z + dir.z * 0.8 };

  const shot = player.dimension.spawnEntity(SHOT, start);
  const projectile = shot.getComponent("minecraft:projectile");
  projectile.owner = player;   // so a hit counts as Adam's, not the world's
  projectile.shoot(
    { x: dir.x * SHOT_SPEED, y: dir.y * SHOT_SPEED, z: dir.z * SHOT_SPEED },
    { uncertainty: SHOT_SPREAD }
  );
  player.dimension.playSound("random.splash", head, { volume: 0.3, pitch: 1.8 });
}

world.afterEvents.itemUse.subscribe(({ source: player, itemStack }) => {
  if (itemStack?.typeId !== BLASTER) return;

  const now = system.currentTick;
  if (now - (lastShot.get(player.id) ?? -FIRE_DELAY) < FIRE_DELAY) return;
  lastShot.set(player.id, now);

  const inv = player.getComponent("minecraft:inventory")?.container;
  const item = inv?.getItem(player.selectedSlotIndex);
  const tank = item?.getComponent("minecraft:durability");
  if (!tank) return;

  // Durability "damage" = water used up. Stop one short of the max so the
  // game never decides the blaster is broken and deletes it.
  const empty = tank.damage >= tank.maxDurability - 1;

  if (tank.damage > 0 && lookingAtWater(player)) {
    tank.damage = 0;
    inv.setItem(player.selectedSlotIndex, item);
    player.dimension.playSound("bucket.fill_water", player.location);
    player.onScreenDisplay.setActionBar("§bWater Blaster refilled!");
    return;
  }

  if (empty) {
    player.dimension.playSound("random.click", player.location, { pitch: 0.6 });
    player.onScreenDisplay.setActionBar("§7Out of water! Look at some water and use it to refill.");
    return;
  }

  try {
    fire(player);
  } catch (e) {
    return; // couldn't spawn the shot — don't use up water for nothing
  }
  tank.damage += 1;
  inv.setItem(player.selectedSlotIndex, item);
});

// ---- What a shot does when it lands ----

world.afterEvents.projectileHitEntity.subscribe((event) => {
  if (!isShot(event.projectile)) return;
  splash(event.dimension, event.location);

  const target = event.getEntityHit()?.entity;
  if (!target) return;
  try {
    target.extinguishFire();
    if (WATER_HATERS.has(target.typeId)) {
      target.applyDamage(WATER_HATER_BONUS, { damagingEntity: event.source });
    }
  } catch (e) { /* mob already gone */ }
});

world.afterEvents.projectileHitBlock.subscribe((event) => {
  if (!isShot(event.projectile)) return;
  splash(event.dimension, event.location);

  const hit = event.getBlockHit()?.block;
  if (!hit) return;
  const r = PUT_OUT_RADIUS;
  for (let x = -r; x <= r; x++) {
    for (let y = -r; y <= r + 1; y++) {
      for (let z = -r; z <= r; z++) {
        try {
          const block = hit.offset({ x, y, z });
          if (block && FIRE_BLOCKS.has(block.typeId)) {
            block.setType("minecraft:air");
          }
        } catch (e) { /* edge of the loaded world */ }
      }
    }
  }
});
