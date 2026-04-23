import test from "node:test";
import assert from "node:assert/strict";

import { ApiError, formatApiErrorMessage } from "../src/lib/api.js";

test("formatApiErrorMessage flattens FastAPI validation arrays into readable text", function () {
  const detail = [
    {
      type: "missing",
      loc: ["body", "monthly_rent_minor"],
      msg: "Field required",
      input: null
    },
    {
      type: "greater_than_equal",
      loc: ["body", "minimum_tenant_score"],
      msg: "Input should be greater than or equal to 0",
      input: -1
    }
  ];

  assert.equal(
    formatApiErrorMessage(detail),
    "body > monthly_rent_minor: Field required; body > minimum_tenant_score: Input should be greater than or equal to 0"
  );
});

test("ApiError always exposes a string message", function () {
  const error = new ApiError([{ msg: "Field required", loc: ["body", "email"] }], 422, null);

  assert.equal(error.message, "Request failed.");
});
