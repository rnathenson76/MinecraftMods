// ============================================================
//  CHOPPER  —  doors + vertical flight   (Adam's script)
// ============================================================
//
// Flying (built-in components): move joystick = fly flat, JUMP = climb.
//
// This script adds the vertical feel + the doors:
//   - HOLD JUMP                 -> climb (built-in)
//   - let go + look ~level      -> HOVER: hold altitude (fly flat or sit still)
//   - let go + look down        -> descend (look at the ground to land)
//   - DOORS: closed while ridden, open when empty
//   - parked (empty) helicopters are held still so a hit can't launch them

import { world, system, InputButton, ButtonState } from "@minecraft/server";

const CHOPPER = "vehicles:chopper";
const DOOR_SWITCH = "vehicles:doors_open";
const DIMENSIONS = ["overworld", "nether", "the_end"];

// ---- Feel (tweak these!) ----
const LOOK_DOWN_ANGLE = 40;  // look down past this many degrees to descend
const SINK_PUSH = 0.09;      // how hard it sinks when you look down
const MAX_SINK  = 0.40;      // fastest sink (blocks per tick)
const HOVER_DAMP = 0.5;      // how strongly it cancels drift to hold altitude

system.runInterval(() => {
  const occupied = new Set();

  // -------- PILOTS: vertical control --------
  for (const player of world.getAllPlayers()) {
    const chopper = player.getComponent("minecraft:riding")?.entityRidingOn;
    if (!chopper || chopper.typeId !== CHOPPER) continue;
    occupied.add(chopper.id);

    try {
      const holdingJump =
        player.inputInfo.getButtonState(InputButton.Jump) === ButtonState.Pressed;
      const pitch = player.getRotation().x; // +90 = looking straight down
      const v = chopper.getVelocity();

      if (holdingJump) {
        // built-in climb handles going up — nothing to do here
      } else if (pitch > LOOK_DOWN_ANGLE) {
        // looking down -> descend
        if (v.y > -MAX_SINK) {
          chopper.applyImpulse({ x: 0, y: -SINK_PUSH, z: 0 });
        }
      } else {
        // looking level/up -> HOVER: cancel any up/down drift, hold altitude
        if (Math.abs(v.y) > 0.02) {
          chopper.applyImpulse({ x: 0, y: -v.y * HOVER_DAMP, z: 0 });
        }
      }
    } catch (e) {
      // input hiccup — doors still work
    }
  }

  // -------- DOORS + park empties still --------
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
        if (shouldBeOpen) {
          chopper.clearVelocity(); // empty + no gravity: keep it from drifting off
        }
      } catch (e) { /* not ready yet */ }
    }
  }
}, 1);
