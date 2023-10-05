/**
 * Returns true iff the "speedrun" requirement of the smaragdine tablet would be satisfied if the player picks it up
 * right now, i.e. if there are at least 600 days left in the spectre of the end's timer.
 * @return {boolean} true iff the "speedrun" requirement of the smaragdine tablet is satisfied
 */
function tabletSpeedrun() {
	return (900 - State.variables.time + State.variables.endSpectre) >= 600 || State.variables.endSpectre < 0;
}

/**
 * Returns true iff the "world record" requirement of the smaragdine tablet would be satisfied if the player picks it up
 * right now, i.e. if there are at least 600 days left in the spectre of the end's timer.
 * @return {boolean} true iff the "world record" requirement of the smaragdine tablet is satisfied
 */
function tabletWorldRecord() {
	return (900 - State.variables.time + State.variables.endSpectre) >= 710 || State.variables.endSpectre < 0;
}

/**
 * Returns true iff the "TAS" requirement of the smaragdine tablet would be satisfied if the player picks it up
 * right now, i.e. if there are at least 600 days left in the spectre of the end's timer.
 * @return {boolean} true iff the "TAS" requirement of the smaragdine tablet is satisfied
 */
function tabletTAS() {
	return (900 - State.variables.time + State.variables.endSpectre) >= 750 || State.variables.endSpectre < 0;
}

/**
 * Returns true iff the "OTP" requirement of the smaragdine tablet would be satisfied if the player picks it up right
 * now, i.e. if there is exactly one hired companion.
 * @return {boolean} true iff the "OTP" requirement of the smaragdine tablet is satisfied
 */
function tabletOTP() {
	return State.variables.hiredCompanions
	            .concat(State.variables.desertedCompanions)
	            .concat(State.variables.LostCompanions)
	            .filter(c => ![setup.companionIds.ai,
	                           setup.companionIds.twin,
	                           setup.companionIds.bandit,
	                           setup.companionIds.golem].includes(c.id)).length === 1;
}

/**
 * Returns true iff the "Single Player" requirement of the smaragdine tablet would be satisfied if the player picks it up right
 * now, i.e. if there is no hired companion.
 * @return {boolean} true iff the "Single Player" requirement of the smaragdine tablet is satisfied
 */
function tabletSinglePlayer() {
	return State.variables.hiredCompanions
	            .concat(State.variables.desertedCompanions)
	            .concat(State.variables.LostCompanions)
	            .filter(c => ![setup.companionIds.ai,
	                           setup.companionIds.twin,
	                           setup.companionIds.bandit,
	                           setup.companionIds.golem].includes(c.id)).length === 0;
}

/**
 * Returns true iff the "Gourmet" requirement of the smaragdine tablet would be satisfied if the player picks it up right
 * now, i.e. if they ate one of every food or drink in the game.
 * @return {boolean} true iff the "Single Player" requirement of the smaragdine tablet is satisfied
 */
function tabletGourmet() {
	return Object.getOwnPropertyNames(State.variables.smaragdineFoodConsumed)
	             .map(p => State.variables.smaragdineFoodConsumed[p])
	             .reduce((a, b) => a && b, true) &&
	       Object.getOwnPropertyNames(State.variables)
	             .filter(p => p.startsWith('waterL'))
	             .map(p => State.variables[p] > 0)
	             .reduce((a, b) => a && b, true) &&
	       Object.getOwnPropertyNames(State.variables)
	             .filter(p => p.startsWith('foodL'))
	             .map(p => State.variables[p] > 0)
	             .reduce((a, b) => a && b, true)
}
