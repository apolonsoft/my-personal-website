---
title: "Designing an API for a list view"
description: "Working backward from a screen to decide which fields, filters, and defaults an endpoint needs."
pubDate: 2026-08-18
category: Engineering
heroImage: /images/studio.webp
imageAlt: A bright studio with a long wooden desk beside a wall of windows.
---

A list of posts looks simple until the first empty page, the first slow response, or two posts published on the same day. I like to settle those cases on paper before writing the query.

My starting point is the row itself. For a blog index it needs a title, a stable link, a publication date, and sometimes a short description. Sending the full article with every row makes the response larger and gives the list another shape of content to handle.

## Choose an order you can repeat

Newest first sounds precise until two entries share a timestamp. I add a stable identifier as a second sort field. Fetching the same page twice then gives me the same order as long as the underlying collection stays the same.

For a growing list, a cursor can carry that pair of values into the next request. The client can use the returned cursor without needing to understand how the database compares it.

## Write the empty response first

I use the same shape for an empty list and a full one. An empty array means the request succeeded and the current filter has no matches. A failed request gets an error state with a retry action.

That distinction matters on the screen. A person who chose a quiet category can change the filter. A person whose connection dropped can try the same request again.
