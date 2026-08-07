// ============================================================
//  CHOPPER  —  doors + descend   (Adam's script)
// ============================================================
//
// Flying uses the helicopter's built-in flight components:
//   - move joystick = fly forward / back / strafe on the flat plane
//   - JUMP (hold)   = rise straight up
//   - let go of jump = gently sink back down   <-- handled here
//
// (On touch there's no separate "down" button while riding — that button is
//  the get-out button — so "let go of jump to sink" is the safe way down.)
//
// This script does two jobs:
//   1) DOORS: closed while someone is riding, open when empty.
//   2) SINK: while riding and NOT holding jump, drift gently downward.

import { world, system, InputButton, ButtonState } from "@minecraft/server";

const CHOPPER = "vehicles:chopper";
const DOOR_SWITCH = "vehicles:doors_open";
const DIMENSIONS = ["overworld", "nether", "the_end"];

// ---- Sink feel (tweak these!) ----
const SINK_PUSH = 0.05; // how hard it drifts down when you're not holding jump
const SINK_MAX  = 0.22; // fastest gentle sink (blocks per tick)

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
        const v = chopper.getVelocity();
        if (v.y > -SINK_MAX) {
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
      } catch (e) { /* not ready yet */ }
    }
  }
}, 1);
