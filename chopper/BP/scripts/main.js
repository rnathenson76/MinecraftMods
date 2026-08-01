// ============================================================
//  CHOPPER DOORS  —  Adam's first Minecraft script!
// ============================================================
//
// The problem: the helicopter's doors can't tell, on their own, when someone
// climbs inside. So this little program does the checking for them.
//
// A few times every second it asks: "Is a player riding a Chopper right now?"
//   - If YES  -> tell that Chopper to CLOSE its doors.
//   - If EMPTY -> tell it to OPEN its doors (so you can hop in).
//
// The 3D model is watching an on/off switch we named "vehicles:doors_open".
// This script just flips that switch. The animation handles the swinging.
//
// Want to experiment? Try changing the 10 near the bottom (that's how often it
// checks, in game-ticks — there are 20 ticks per second). Smaller = snappier.

import { world, system } from "@minecraft/server";

const CHOPPER = "vehicles:chopper";      // the helicopter's id
const DOOR_SWITCH = "vehicles:doors_open"; // the on/off switch the model watches
const DIMENSIONS = ["overworld", "nether", "the_end"];

system.runInterval(() => {
  // 1) Find every Chopper that currently has a rider.
  const occupied = new Set();
  for (const player of world.getAllPlayers()) {
    const vehicle = player.getComponent("minecraft:riding")?.entityRidingOn;
    if (vehicle && vehicle.typeId === CHOPPER) {
      occupied.add(vehicle.id);
    }
  }

  // 2) Update every Chopper: doors CLOSED if someone's aboard, OPEN if empty.
  for (const dimensionId of DIMENSIONS) {
    let choppers;
    try {
      choppers = world.getDimension(dimensionId).getEntities({ type: CHOPPER });
    } catch (e) {
      continue; // that dimension isn't loaded right now — skip it
    }
    for (const chopper of choppers) {
      const shouldBeOpen = !occupied.has(chopper.id);
      try {
        // only flip the switch if it actually needs to change
        if (chopper.getProperty(DOOR_SWITCH) !== shouldBeOpen) {
          chopper.setProperty(DOOR_SWITCH, shouldBeOpen);
        }
      } catch (e) {
        // the chopper isn't fully ready yet — we'll catch it next time
      }
    }
  }
}, 10); // <-- check every 10 ticks (about twice a second)
