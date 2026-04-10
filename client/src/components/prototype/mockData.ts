import type { RoomData } from "@/components/gen-ui-compopnents/RoomCard"

// Mock rooms using real room data (names, types, prices) with fake date_ranges for prototype
export const MOCK_ROOMS: RoomData[] = [
  {
    id: 18, room_name: "S1", room_type: "Family Sea View Bungalow",
    summary: "Sea view family bungalow with 2 bedrooms, 2 bathrooms. Warm atmosphere, private balcony with full ocean view.",
    bed_queen: 1, bed_single: 2, baths: 2, size: 32, max_guests: 4,
    price_weekdays: 4200, price_weekends_holidays: 4400, price_ny_songkran: 4700,
    steps_to_beach: 7, sea_view: 8, privacy: 8, steps_to_restaurant: 6,
    room_design: 0, room_newness: 0, tags: ["family", "sea view"],
    date_ranges: [{ start: "2026-04-14", end: "2026-04-22" }, { start: "2026-05-01", end: "2026-05-10" }],
  },
  {
    id: 19, room_name: "S2", room_type: "Family Sea View Bungalow",
    summary: "Sea view family bungalow for up to 4 guests. 2 bedrooms, 2 bathrooms with comfortable beds and private balcony.",
    bed_queen: 1, bed_single: 2, baths: 2, size: 32, max_guests: 4,
    price_weekdays: 4200, price_weekends_holidays: 4400, price_ny_songkran: 4700,
    steps_to_beach: 7, sea_view: 8, privacy: 8, steps_to_restaurant: 6,
    room_design: 0, room_newness: 0, tags: ["family", "sea view"],
    date_ranges: [{ start: "2026-04-12", end: "2026-04-18" }],
  },
  {
    id: 20, room_name: "S3", room_type: "Sea View Bungalow",
    summary: "Wooden sea view bungalow surrounded by nature. Glass doors open to ocean views, private balcony for relaxation.",
    bed_queen: 1, bed_single: 0, baths: 1, size: 16, max_guests: 2,
    price_weekdays: 2200, price_weekends_holidays: 2400, price_ny_songkran: 2700,
    steps_to_beach: 7, sea_view: 8, privacy: 8, steps_to_restaurant: 6,
    room_design: 0, room_newness: 0, tags: ["sea view", "couple"],
    date_ranges: [{ start: "2026-04-14", end: "2026-04-22" }, { start: "2026-05-03", end: "2026-05-12" }],
  },
  {
    id: 21, room_name: "S4", room_type: "Sea View Bungalow",
    summary: "Natural wooden bungalow nestled among trees and rocks. Open-air bathroom, private balcony with sea view.",
    bed_queen: 1, bed_single: 0, baths: 1, size: 16, max_guests: 2,
    price_weekdays: 2200, price_weekends_holidays: 2400, price_ny_songkran: 2700,
    steps_to_beach: 7, sea_view: 9, privacy: 8, steps_to_restaurant: 5,
    room_design: 0, room_newness: 0, tags: ["sea view", "nature"],
    date_ranges: [{ start: "2026-04-15", end: "2026-04-25" }],
  },
  {
    id: 22, room_name: "S5", room_type: "Sea View Bungalow",
    summary: "Sea view bungalow surrounded by lush trees. Large balcony with dining set, spacious modern bathroom.",
    bed_queen: 1, bed_single: 0, baths: 1, size: 16, max_guests: 2,
    price_weekdays: 2200, price_weekends_holidays: 2400, price_ny_songkran: 2700,
    steps_to_beach: 6, sea_view: 7, privacy: 7, steps_to_restaurant: 4,
    room_design: 0, room_newness: 0, tags: ["sea view", "couple"],
    date_ranges: [{ start: "2026-04-14", end: "2026-04-22" }],
  },
  {
    id: 23, room_name: "S6", room_type: "Good Sea View Bungalow",
    summary: "Oceanfront bungalow with 2-level balcony and private beach access. Open-air bathroom, panoramic views.",
    bed_queen: 1, bed_single: 0, baths: 1, size: 16, max_guests: 2,
    price_weekdays: 2530, price_weekends_holidays: 2800, price_ny_songkran: 3100,
    steps_to_beach: 6, sea_view: 9, privacy: 9, steps_to_restaurant: 9,
    room_design: 0, room_newness: 0, tags: ["premium view", "private beach access"],
    date_ranges: [{ start: "2026-04-12", end: "2026-04-20" }, { start: "2026-05-01", end: "2026-05-10" }],
  },
  {
    id: 24, room_name: "S7", room_type: "Good Sea View Bungalow",
    summary: "Hidden among trees with sea views. 2-level balcony, private beach access, open-air bathroom. Ultimate privacy.",
    bed_queen: 1, bed_single: 0, baths: 1, size: 16, max_guests: 2,
    price_weekdays: 2530, price_weekends_holidays: 2800, price_ny_songkran: 3100,
    steps_to_beach: 5, sea_view: 9, privacy: 10, steps_to_restaurant: 10,
    room_design: 0, room_newness: 0, tags: ["premium view", "most private"],
    date_ranges: [{ start: "2026-04-14", end: "2026-04-22" }],
  },
  {
    id: 25, room_name: "S8", room_type: "Romantic Sea View Bungalow",
    summary: "Romantic beachfront bungalow for couples. Panoramic ocean view balcony, sunrise from bed, near beach steps.",
    bed_queen: 1, bed_single: 0, baths: 1, size: 20, max_guests: 2,
    price_weekdays: 2900, price_weekends_holidays: 3200, price_ny_songkran: 3500,
    steps_to_beach: 9, sea_view: 10, privacy: 8, steps_to_restaurant: 6,
    room_design: 0, room_newness: 0, tags: ["romantic", "best sea view"],
    date_ranges: [{ start: "2026-04-15", end: "2026-04-25" }, { start: "2026-05-03", end: "2026-05-12" }],
  },
  {
    id: 26, room_name: "S9", room_type: "Deluxe Romantic Sea View Bungalow",
    summary: "The closest bungalow to the sea and beach. Panoramic view, sunbed balcony, stone bathroom. Perfect for honeymoon.",
    bed_queen: 1, bed_single: 0, baths: 1, size: 20, max_guests: 2,
    price_weekdays: 3160, price_weekends_holidays: 3500, price_ny_songkran: 3900,
    steps_to_beach: 10, sea_view: 10, privacy: 8, steps_to_restaurant: 9,
    room_design: 0, room_newness: 0, tags: ["deluxe romantic", "closest to beach"],
    date_ranges: [{ start: "2026-04-12", end: "2026-04-18" }, { start: "2026-04-25", end: "2026-05-05" }],
  },
  {
    id: 27, room_name: "S10", room_type: "Mini Family Happy Love 1",
    summary: "2-story family bungalow for 3 guests. Glass-walled upper bedroom with tree-top and sea views. Private balcony.",
    bed_queen: 1, bed_single: 1, baths: 1, size: 28, max_guests: 3,
    price_weekdays: 3300, price_weekends_holidays: 3600, price_ny_songkran: 3900,
    steps_to_beach: 6, sea_view: 6, privacy: 7, steps_to_restaurant: 4,
    room_design: 0, room_newness: 0, tags: ["family", "2-story"],
    date_ranges: [{ start: "2026-04-14", end: "2026-04-22" }],
  },
  {
    id: 28, room_name: "S11", room_type: "Double Deluxe Happy Love",
    summary: "Garden and sea atmosphere bungalow. Private wooden balcony among birdsong and sea breeze. 2-3 min walk to beach.",
    bed_queen: 1, bed_single: 0, baths: 1, size: 18, max_guests: 2,
    price_weekdays: 1990, price_weekends_holidays: 2200, price_ny_songkran: 2500,
    steps_to_beach: 5, sea_view: 5, privacy: 7, steps_to_restaurant: 2,
    room_design: 0, room_newness: 0, tags: ["value", "garden view"],
    date_ranges: [{ start: "2026-04-12", end: "2026-04-20" }, { start: "2026-04-22", end: "2026-05-02" }],
  },
  {
    id: 29, room_name: "S12", room_type: "Junior Family Bungalow",
    summary: "Compact family bungalow with 2 bedrooms. Close to restaurant, wide balcony with sea view and swing chair.",
    bed_queen: 1, bed_single: 2, baths: 1, size: 28, max_guests: 4,
    price_weekdays: 3300, price_weekends_holidays: 3600, price_ny_songkran: 3900,
    steps_to_beach: 5, sea_view: 5, privacy: 7, steps_to_restaurant: 2,
    room_design: 0, room_newness: 0, tags: ["family", "convenient"],
    date_ranges: [{ start: "2026-04-14", end: "2026-04-22" }, { start: "2026-05-01", end: "2026-05-10" }],
  },
  {
    id: 30, room_name: "S14", room_type: "Junior Family Bungalow",
    summary: "Family bungalow with 2 bedrooms. Easy walk to restaurant, natural wood interior, sea view balcony.",
    bed_queen: 1, bed_single: 2, baths: 1, size: 28, max_guests: 4,
    price_weekdays: 3300, price_weekends_holidays: 3600, price_ny_songkran: 3900,
    steps_to_beach: 5, sea_view: 5, privacy: 7, steps_to_restaurant: 3,
    room_design: 0, room_newness: 0, tags: ["family", "convenient"],
    date_ranges: [{ start: "2026-04-15", end: "2026-04-25" }],
  },
  {
    id: 31, room_name: "V1", room_type: "Family Good View Bungalow",
    summary: "The only family bungalow closest to the sea. Panoramic glass bedroom, huge seaside balcony. 2 bedrooms.",
    bed_queen: 2, bed_single: 1, baths: 0, size: 32, max_guests: 4,
    price_weekdays: 4700, price_weekends_holidays: 5000, price_ny_songkran: 5490,
    steps_to_beach: 6, sea_view: 10, privacy: 9, steps_to_restaurant: 8,
    room_design: 0, room_newness: 0, tags: ["premium", "closest to sea", "family"],
    date_ranges: [{ start: "2026-04-12", end: "2026-04-18" }, { start: "2026-05-01", end: "2026-05-10" }],
  },
  {
    id: 32, room_name: "V2", room_type: "Double Family Good View Bungalow",
    summary: "Spacious family bungalow with 2 bedrooms, 2 bathrooms. Large sea view balcony with seating area.",
    bed_queen: 1, bed_single: 2, baths: 2, size: 36, max_guests: 4,
    price_weekdays: 4400, price_weekends_holidays: 4700, price_ny_songkran: 5000,
    steps_to_beach: 9, sea_view: 8, privacy: 8, steps_to_restaurant: 7,
    room_design: 0, room_newness: 0, tags: ["family", "spacious"],
    date_ranges: [{ start: "2026-04-14", end: "2026-04-22" }],
  },
  {
    id: 33, room_name: "V3", room_type: "Deluxe Good View Bungalow",
    summary: "Romantic bungalow hidden in nature. Canopy bed, glass sliding doors to sea view balcony. Near snorkeling beach.",
    bed_queen: 1, bed_single: 0, baths: 1, size: 20, max_guests: 2,
    price_weekdays: 2530, price_weekends_holidays: 2800, price_ny_songkran: 3100,
    steps_to_beach: 9, sea_view: 9, privacy: 8, steps_to_restaurant: 7,
    room_design: 0, room_newness: 0, tags: ["romantic", "nature"],
    date_ranges: [{ start: "2026-04-15", end: "2026-04-25" }, { start: "2026-05-03", end: "2026-05-12" }],
  },
]

export const MAP_LARGE = "/static/photos/maps/resort_map.jpeg"
export const MAP_SMALL = "/static/photos/maps/resort_map_sm.jpg"

// Pin positions as percentages of the map image (1448x2048)
// Positioned to overlay the room name labels already on the map
export const ROOM_PIN_POSITIONS: Record<number, { x: number; y: number }> = {
  18: { x: 88.4, y: 47.6 },   // S1
  19: { x: 66.5, y: 47.4 },   // S2
  20: { x: 8.8, y: 50.2 },   // S3
  21: { x: 25.6, y: 69.7 },   // S4
  22: { x: 40.6, y: 47 },   // S5
  23: { x: 44, y: 85.6 },   // S6
  24: { x: 8.2, y: 87 },   // S7
  25: { x: 70.7, y: 68.3 },   // S8
  26: { x: 56.3, y: 86.4 },   // S9
  27: { x: 9.7, y: 36.7 },   // S10
  28: { x: 29.8, y: 34.5 },   // S11
  29: { x: 61.5, y: 38 },   // S12
  30: { x: 82.1, y: 38.4 },   // S14
  31: { x: 26.1, y: 87.2 },   // V1
  32: { x: 50.9, y: 69.9 },   // V2
  33: { x: 92.9, y: 58.8 },   // V3
}