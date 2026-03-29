import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import Icon from "../Icon.vue";

describe("Icon", () => {
  it("renders the path for a known icon name", () => {
    const wrapper = mount(Icon, {
      props: { name: "check" },
      attrs: { class: "h-4 w-4", "aria-hidden": "true" },
    });
    const svg = wrapper.find("svg");
    expect(svg.exists()).toBe(true);
    expect(svg.classes()).toContain("h-4");
    expect(svg.classes()).toContain("w-4");
    expect(svg.find("path").exists()).toBe(true);
  });
});
