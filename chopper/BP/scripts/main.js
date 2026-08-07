// ============================================================
//  CHOPPER  —  doors + descend   (Adam's script)
// ============================================================
//
// Flying is now handled by the helicopter's built-in flight components:
//   - move joystick  = fly forward / back / strafe on the flat plane
//   - jump button    = rise straight up (and it no longer kicks you out!)
//   - let go         = hover (no gravity)
//
// This script adds the two things those components don't do on their own:
//   1) DOORS: closed while someone is riding, open when empty.
//   2) DESCEND: hold the sneak / down control to sink back down.

import { world, system, InputButton, ButtonState } from "@minecraft/server";

const CHOPPER = "vehicles:chopper";
const DOOR_SWITCH = "vehicles:doors_open";
const DIMENSIONS = ["overworld", "nether", "the_end"];

// ---- Descend feel (tweak these!) ----
const DESCEND_PUSH = 0.18; // how hard the down control pushes each tick
const MAX_DESCEND  = 0.45; // fastest it will sink (blocks per tick)

system.runInterval(() => {
  const occupied = new Set();

  // -------- PILOTS: let them sink with the down control --------
  for (const player of world.getAllPlayers()) {
    const chopper = player.getComponent("minecraft:riding")?.entityRidingOn;
    if (!chopper || chopper.typeId !== CHOPPER) continue;
    occupied.add(chopper.id);

    try {
      const holdingDown =
        player.inputInfo.getButtonState(InputButton.Sneak) === ButtonState.Pressed;
      if (holdingDown) {
        const v = chopper.getVelocity();
        if (v.y > -MAX_DESCEND) {
          chopper.applyImpulse({ x: 0, y: -DESCEND_PUSH, z: 0 });
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
