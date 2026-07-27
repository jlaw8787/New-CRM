// Travel document parser, Build C step 1, backend only.
// Accepts one uploaded doc (base64 image or PDF), reads it with Claude
// server side, and returns structured flight, accommodation, car and
// expense fields. The Anthropic key lives only in this function's
// environment, set as a Supabase secret, never in index.html or git.
import Anthropic from "npm:@anthropic-ai/sdk";

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

// Field names match the Manage Placement draft objects (MPFlight, MPAccom,
// MPCar, MPExpense) so the step 2 pre-fill is a plain assignment, no
// remapping. json_schema forces valid JSON back, so the model cannot wrap
// the answer in prose or markdown fences, and required string fields plus
// the system prompt below keep it from guessing a value it cannot read.
const EXTRACTION_SCHEMA = {
  type: "object",
  properties: {
    flights: {
      type: "array",
      items: {
        type: "object",
        properties: {
          airline: { type: "string" },
          flightNo: { type: "string" },
          from: { type: "string" },
          to: { type: "string" },
          departDate: { type: "string", description: "ISO date, YYYY-MM-DD, empty string if not found" },
          returnDate: { type: "string", description: "ISO date, YYYY-MM-DD, empty string if not found" },
          bookingRef: { type: "string" },
          cost: { type: "string" },
        },
        required: ["airline", "flightNo", "from", "to", "departDate", "returnDate", "bookingRef", "cost"],
        additionalProperties: false,
      },
    },
    accommodation: {
      type: "array",
      items: {
        type: "object",
        properties: {
          name: { type: "string" },
          address: { type: "string" },
          checkIn: { type: "string", description: "ISO date, YYYY-MM-DD, empty string if not found" },
          checkOut: { type: "string", description: "ISO date, YYYY-MM-DD, empty string if not found" },
          bookingRef: { type: "string" },
          cost: { type: "string" },
          costUnit: { type: "string", description: "e.g. per night, empty string if not found" },
        },
        required: ["name", "address", "checkIn", "checkOut", "bookingRef", "cost", "costUnit"],
        additionalProperties: false,
      },
    },
    carHire: {
      type: "array",
      items: {
        type: "object",
        properties: {
          provider: { type: "string" },
          vehicle: { type: "string" },
          pickupLocation: { type: "string" },
          pickupDate: { type: "string", description: "ISO date, YYYY-MM-DD, empty string if not found" },
          returnDate: { type: "string", description: "ISO date, YYYY-MM-DD, empty string if not found" },
          bookingRef: { type: "string" },
          cost: { type: "string" },
          costUnit: { type: "string", description: "e.g. per day, empty string if not found" },
        },
        required: ["provider", "vehicle", "pickupLocation", "pickupDate", "returnDate", "bookingRef", "cost", "costUnit"],
        additionalProperties: false,
      },
    },
    expenses: {
      type: "array",
      items: {
        type: "object",
        properties: {
          type: { type: "string" },
          amount: { type: "string" },
          description: { type: "string" },
          date: { type: "string", description: "ISO date, YYYY-MM-DD, empty string if not found" },
          receiptRef: { type: "string" },
        },
        required: ["type", "amount", "description", "date", "receiptRef"],
        additionalProperties: false,
      },
    },
  },
  required: ["flights", "accommodation", "carHire", "expenses"],
  additionalProperties: false,
};

const SYSTEM_PROMPT = "You read travel documents for a travel nursing agency: airline "
  + "e-tickets, hotel confirmations, agent itineraries, booking emails, screenshots, "
  + "mixed PDFs. One document can hold more than one record and more than one type. "
  + "Read the whole document in one pass and extract every flight, every "
  + "accommodation booking, every car hire and every expense you find, across all "
  + "four types, do not assume the document is only one type. "
  + "Return only the structured fields defined by the schema, no preamble, no "
  + "commentary, no markdown fences. "
  + "If a field is not present in the document, leave it as an empty string, never "
  + "guess or infer a value that is not actually written in the document.";

const EMPTY_RESULT = { flights: [], accommodation: [], carHire: [], expenses: [] };

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: CORS_HEADERS });
  }
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "POST only" }), {
      status: 405,
      headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }
  try {
    const body = await req.json();
    const data = body && body.data;
    const mediaType = body && body.mediaType;
    if (!data || !mediaType) {
      return new Response(JSON.stringify({ error: "Missing data or mediaType" }), {
        status: 400,
        headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
      });
    }

    const client = new Anthropic({ apiKey: Deno.env.get("ANTHROPIC_API_KEY") });
    const docBlock = mediaType === "application/pdf"
      ? { type: "document", source: { type: "base64", media_type: mediaType, data } }
      : { type: "image", source: { type: "base64", media_type: mediaType, data } };

    const response = await client.messages.create({
      model: "claude-opus-5",
      max_tokens: 4096,
      thinking: { type: "adaptive" },
      output_config: {
        effort: "medium",
        format: { type: "json_schema", schema: EXTRACTION_SCHEMA },
      },
      system: SYSTEM_PROMPT,
      messages: [{
        role: "user",
        content: [
          docBlock,
          { type: "text", text: "Extract every travel record from this document into the given shape." },
        ],
      }],
    });

    if (response.stop_reason === "refusal") {
      return new Response(JSON.stringify({ error: "Model declined to process this document" }), {
        status: 422,
        headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
      });
    }

    const textBlock = response.content.find((b) => b.type === "text");
    const parsed = textBlock ? JSON.parse(textBlock.text) : EMPTY_RESULT;

    return new Response(JSON.stringify(parsed), {
      headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  } catch (e) {
    const message = e && e.message ? e.message : String(e);
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }
});
