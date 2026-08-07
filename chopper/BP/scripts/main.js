// ============================================================
//  CHOPPER  —  doors + descend   (Adam's script)
// ============================================================
//
// Flying uses the helicopter's built-in flight components:
//   - move joystick = fly forward / back / strafe on the flat plane
//   - JUMP (hold)   = climb straight up
//   - let go of jump = sink gently back down   <-- handled here
//
// This script does two jobs:
//   1) DOORS: closed while someone is riding, open when empty.
//   2) SINK: while riding and NOT holding jump, ease downward until the
//      Chopper is resting on the ground or water.

import { world, system, InputButton, ButtonState } from "@minecraft/server";

const CHOPPER = "vehicles:chopper";
const DOOR_SWITCH = "vehicles:doors_open";
const DIMENSIONS = ["overworld", "nether", "the_end"];

// ---- Sink feel (tweak this!) ----
const SINK_PER_TICK = 0.13; // blocks it drops each tick when you're not climbing

system.runInterval(() => {
  const occupied = new Set();

  // -------- PILOTS: sink when not holding jump --------
  for (const player of world.getAllPlayers()) {
    const chopper = player.getComponent("minecraft:riding")?.entityRidingOn;
    if (!chopper || chopper.typeId !== CHOPPER) continue;
    occupied.add(chopper.id);

    try {
      const holdingJump =
        player.inputInfo.getButtonState(InputButton.Jump) === ButtonState.Pressed;
      if (!holdingJump) {
        const loc = chopper.location;
        const targetY = loc.y - SINK_PER_TICK;
        // don't sink into solid ground / water — rest on top of it
        const below = chopper.dimension.getBlock({
          x: Math.floor(loc.x), y: Math.floor(targetY), z: Math.floor(loc.z)
        });
        if (below && below.isAir) {
          chopper.teleport(
            { x: loc.x, y: targetY, z: loc.z },
            { keepVelocity: true } // keep flying smoothly sideways while sinking
          );
        }
      }
    } catch (e) {
      // input/lookup hiccup — doors still work
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
}, 1);
