import { test } from 'node:test';
import assert from 'node:assert/strict';
import { REGION_PROFILES, GLOBAL_DATA_FEEDS, AiBotController } from './aiBot.js';

test('REGION_PROFILES carries comprehensive profile for Bangalore with all aliases and feeds', () => {
  assert.ok(REGION_PROFILES.bangalore, 'Bangalore profile exists');
  const b = REGION_PROFILES.bangalore;

  assert.equal(b.id, 'bangalore');
  assert.ok(b.aliases.includes('bangalore'));
  assert.ok(b.aliases.includes('bengaluru'));
  assert.ok(b.aliases.includes('banglore'));
  assert.ok(b.aliases.includes('blr'));

  assert.equal(b.coordinates.lat, 12.9716);
  assert.equal(b.coordinates.lon, 77.5946);
  assert.equal(b.camera.lat, 12.9716);
  assert.equal(b.camera.lon, 77.5946);
  assert.ok(b.camera.altitude >= 1000 && b.camera.altitude <= 5000);

  // Check landmarks
  assert.ok(b.landmarks.length >= 4);
  const landmarkNames = b.landmarks.map((l) => l.name);
  assert.ok(landmarkNames.some((n) => n.includes('Airport')));
  assert.ok(landmarkNames.some((n) => n.includes('Vidhana Soudha')));
  assert.ok(landmarkNames.some((n) => n.includes('UB City')));

  // Check available feeds
  const feedLayerIds = b.availableDataFeeds.map((f) => f.layerId);
  assert.ok(feedLayerIds.includes('flights'), 'Should include flights');
  assert.ok(feedLayerIds.includes('weather'), 'Should include weather');
  assert.ok(feedLayerIds.includes('satellites'), 'Should include satellites');
  assert.ok(feedLayerIds.includes('traffic'), 'Should include traffic');
  assert.ok(feedLayerIds.includes('cctv'), 'Should include cctv');
  assert.ok(feedLayerIds.includes('local-firms'), 'Should include fires');
  assert.ok(feedLayerIds.includes('earthquakes'), 'Should include earthquakes');
});

test('GLOBAL_DATA_FEEDS includes baseline feeds for any worldwide location', () => {
  assert.ok(GLOBAL_DATA_FEEDS.length >= 6);
  const layerIds = GLOBAL_DATA_FEEDS.map((f) => f.layerId);
  assert.ok(layerIds.includes('flights'));
  assert.ok(layerIds.includes('weather'));
  assert.ok(layerIds.includes('satellites'));
  assert.ok(layerIds.includes('earthquakes'));
});

test('AiBotController query extraction correctly parses user intents', () => {
  // Mock lightweight controller prototype
  const controller = Object.create(AiBotController.prototype);

  assert.equal(controller._extractRegionName('I want Bangalore data'), 'bangalore');
  assert.equal(controller._extractRegionName('i want banglore data'), 'banglore');
  assert.equal(controller._extractRegionName('show me data for tokyo'), 'tokyo');
  assert.equal(controller._extractRegionName('give me London data'), 'london');
  assert.equal(controller._extractRegionName('fly to Paris'), 'paris');
  assert.equal(controller._extractRegionName('what data do you have for San Francisco'), 'san francisco');
  assert.equal(controller._extractRegionName('Bangalore'), 'bangalore');
});

test('AiBotController resolves aliases to correct profile', async () => {
  const controller = Object.create(AiBotController.prototype);

  const res1 = await controller._resolveRegion('banglore');
  assert.equal(res1?.id, 'bangalore');

  const res2 = await controller._resolveRegion('Bengaluru');
  assert.equal(res2?.id, 'bangalore');

  const res3 = await controller._resolveRegion('tokyo');
  assert.equal(res3?.id, 'tokyo');

  const res4 = await controller._resolveRegion('san francisco');
  assert.equal(res4?.id, 'sanfrancisco');
});
