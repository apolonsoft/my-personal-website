---
title: "When is a component finished?"
description: "The small checks I make between a working prototype and a component I’m happy to reuse."
pubDate: 2026-10-24
category: Development
heroImage: /images/workbench.webp
imageAlt: An open laptop on a wooden desk beside a small potted plant.
---

A button usually looks finished a few minutes after I start it. It has a label, the padding feels right, and clicking it does something. I get a better sense of how much work is left when I put it in a second place.

In a toolbar, that button sits beside a search field. In a form, it waits for a network request. The same rectangle now has two jobs, and the differences tell me what the component needs to own.

## Start with the awkward cases

I replace the label with the longest one I expect to ship. Then I narrow the window, zoom in, and use the page with a keyboard. A focus ring can look perfect in isolation and disappear behind the edge of a scrolling container.

For a submit button, I also slow the request down. I want a second click to be harmless, the pending state to be legible, and a failed request to leave the person’s input intact.

## Give the component a second home

Before adding a variant, I try the component in another real screen. If the only difference is the space around it, the parent layout can own that space. If the two screens need different words, the label can stay an input. Neither case needs a new visual variant.

I call a component finished when its caller can describe the job in a few plain props and its behavior still makes sense when the page gets crowded.
