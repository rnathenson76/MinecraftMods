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

// ---- Sink feel (tweak these!) ----
const SINK_PUSH = 0.09; // how hard it drifts down when you're not holding jump
const MAX_SINK  = 0.40; // fastest it will sink (blocks per tick)

system.runInterval(() => {
  const occupied = new Set();

  // -------- PILOTS: sink when not holding jump --------
  // NOTE: we nudge the velocity down with applyImpulse (never teleport) so the
  // helicopter's facing/steering is left completely alone.
  for (const player of world.getAllPlayers()) {
    const chopper = player.getComponent("minecraft:riding")?.entityRidingOn;
    if (!chopper || chopper.typeId !== CHOPPER) continue;
    occupied.add(chopper.id);

    try {
      const holdingJump =
        player.inputInfo.getButtonState(InputButton.Jump) === ButtonState.Pressed;
      if (!holdingJump) {
        const v = chopper.getVelocity();
        if (v.y > -MAX_SINK) {
          chopper.applyImpulse({ x: 0, y: -SINK_PUSH, z: 0 });
        }
      }
    } catch (e) {
      // input hiccup — doors still work
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
        // Empty + no gravity = a single hit would send it drifting to space.
        // Hold parked (empty) helicopters still so that can't happen.
        if (shouldBeOpen) {
          chopper.clearVelocity();
        }
      } catch (e) { /* not ready yet */ }
    }
  }
}, 1);
