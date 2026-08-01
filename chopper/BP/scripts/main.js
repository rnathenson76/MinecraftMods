// ============================================================
//  CHOPPER  —  doors + FLIGHT   (Adam's scripts)
// ============================================================
//
// Part 1 (doors): a Chopper can't tell on its own when someone climbs in, so
//   we check every tick: if a player is riding -> CLOSE the doors; empty -> OPEN.
//
// Part 2 (flight): while you're the pilot, the Chopper flies WHERE YOU LOOK.
//   - Push the move joystick FORWARD -> fly the way you're looking
//     (look up to climb, look down to dive).
//   - Joystick LEFT / RIGHT -> slide sideways.
//   - JUMP button -> lift straight up.
//   - Let go of everything -> it hovers in place.
//
// The three SPEED numbers below are the fun ones to experiment with.

import { world, system, InputButton, ButtonState } from "@minecraft/server";

const CHOPPER = "vehicles:chopper";
const DOOR_SWITCH = "vehicles:doors_open";
const DIMENSIONS = ["overworld", "nether", "the_end"];

// ---- Flight feel (tweak these!) ----
const FORWARD_SPEED = 0.55; // blocks per tick flying forward (higher = faster)
const STRAFE_SPEED  = 0.35; // blocks per tick sliding sideways
const LIFT_SPEED    = 0.45; // blocks per tick rising when you hold jump

system.runInterval(() => {
  const occupied = new Set();

  // -------- PILOTS: fly their Chopper --------
  for (const player of world.getAllPlayers()) {
    const chopper = player.getComponent("minecraft:riding")?.entityRidingOn;
    if (!chopper || chopper.typeId !== CHOPPER) continue;
    occupied.add(chopper.id);

    try {
      const move = player.inputInfo.getMovementVector(); // {x: strafe, y: forward}
      const view = player.getViewDirection();            // 3D look direction
      const rot  = player.getRotation();                 // {x: pitch, y: yaw}

      // Fly in the direction you're looking, scaled by the forward stick.
      let vx = view.x * move.y * FORWARD_SPEED;
      let vy = view.y * move.y * FORWARD_SPEED;
      let vz = view.z * move.y * FORWARD_SPEED;

      // Strafe: a horizontal vector pointing to the pilot's right.
      const rx = -view.z, rz = view.x;
      const rlen = Math.hypot(rx, rz) || 1;
      vx += (rx / rlen) * move.x * STRAFE_SPEED;
      vz += (rz / rlen) * move.x * STRAFE_SPEED;

      // Jump button = rise straight up.
      if (player.inputInfo.getButtonState(InputButton.Jump) === ButtonState.Pressed) {
        vy += LIFT_SPEED;
      }

      // Move the Chopper, but don't bury its base inside a solid block.
      const loc = chopper.location;
      const dest = { x: loc.x + vx, y: loc.y + vy, z: loc.z + vz };
      const b = chopper.dimension.getBlock({
        x: Math.floor(dest.x), y: Math.floor(dest.y), z: Math.floor(dest.z)
      });
      const blocked = b && !b.isAir && !b.isLiquid;
      if (!blocked && (vx || vy || vz)) {
        chopper.teleport(dest, { rotation: { x: 0, y: rot.y }, keepVelocity: false });
      }
    } catch (e) {
      // input API hiccup — doors still work; just skip flying this tick
    }
  }

  // -------- DOORS: closed if occupied, open if empty --------
  for (const dimensionId of DIMENSIONS) {
    let choppers;
    try { choppers = world.getDimension(dimensionId).getEntities({ type: CHOPPER }); }
    catch (e) { continue; }
    for (const chopper of choppers) {
      const shouldBeOpen = !occupied.has(chopper.id);
      try {
        if (chopper.getProperty(DOOR_SWITCH) !== shouldBeOpen) {
          chopper.setProperty(DOOR_SWITCH, shouldBeOpen);
        }
      } catch (e) { /* not ready yet */ }
    }
  }
}, 1); // every tick, so flight is smooth
