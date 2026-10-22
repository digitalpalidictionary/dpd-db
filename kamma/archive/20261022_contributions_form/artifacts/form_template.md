# Google Form template: Offer your help to DPD

Build this by hand in Google Forms, styled like the other DPD forms. One section, five questions plus the built-in email field. The person makes the offer. The maintainer decides where it goes.

## Form settings

- **Title:** Offer your help to DPD
- **Description:** Thank you for offering to help with the Digital Pāḷi Dictionary. Tell us what you can give and for how long. We read every offer and reply by email. The people who maintain DPD are Buddhist monks. They do not deal with money. Only time, energy, resources and pre-bought services are accepted. Donations are not accepted. By sending this form you agree that DPD may store these details and email you about your offer. Please do not send passwords or login details.
- **Collect email addresses:** Responder input. This is the built-in email field. It must be on, or the "send a copy" setting does not appear. Do NOT add an email question of your own.
- **Send responders a copy:** Always.
- **Limit to 1 response, edit after submit:** Off.
- **Confirmation message:** Thank you. We will reply by email. Your copy of the answers is on its way.
- **Notifications:** Responses tab, "Get email notifications for new responses".
- **Link to sheet:** Responses tab, link to a new sheet. Add a "Status" column at the end by hand: new, replied, accepted, declined, expired.

## Questions

1. **Name.** Short answer. Required.
2. **I can help with.** Checkboxes. Required.
   - Pāḷi
   - Code
   - Resources
   - Other
3. **Tell us about your offer.** Paragraph. Required. Help text: "Tell us in your own words what you would like to offer. For Pāḷi, say your area. For code, say your languages."
4. **How much can you offer?** Short answer. Required. Help text: "Tell us the size of your offer, so we know what fits. For example: 3 hours a week, or one day a month."
5. **How long does your offer last?** Short answer. Required. Help text: "For example: one time only, until March 2027, or ongoing."

## Resources section wording (decided 2026-10-22)

The live form has four sections: About you, Pāḷi, Code and GitHub, Resources. In the Resources section the person may state a budget. The money never goes to DPD. The person buys the subscription themselves, directly from the service, using a login the maintainers give them. The wording must make that direction clear.

- **Section description:** Help with resources and infrastructure. You never send money to DPD. If we accept your offer, you buy the subscription yourself, directly from the service, using a login we give you.
- **Question:** How much would you like to spend on a service for DPD?
- **Help text:** The most you would like to spend. For example: $20 a month, or $200 a year. You pay the service directly. No money is sent to DPD.
- **Question:** How long does your offer last? (unchanged)

## Quotation on money (placement to confirm)

Source: SN42.10 Maṇicūḷakasutta, the passage that contains *tiṇatthika*. Pāḷi from the Mahāsaṅgīti edition on SuttaCentral (ṁ changed to ṃ to match DPD). English by Bhikkhu Sujato (CC0), read from the local SuttaCentral data.

> Api cāhaṃ, gāmaṇi, evaṃ vadāmi: tiṇaṃ tiṇatthikena pariyesitabbaṃ, dāru dārutthikena pariyesitabbaṃ, sakaṭaṃ sakaṭatthikena pariyesitabbaṃ, puriso purisatthikena pariyesitabbo. Na tvevāhaṃ, gāmaṇi, kenaci pariyāyena ‘jātarūparajataṃ sāditabbaṃ pariyesitabban’ti vadāmī”ti.

**Translation:** Rather, chief, I say this: straw may be looked for by one needing straw; wood may be looked for by one needing wood; a cart may be looked for by one needing a cart; a workman may be looked for by one needing a workman. But in any case, there is no way they can accept or look for gold and currency, I say.

- The Pāḷi is shown first, the translation under it.
- The line just before this passage (SN42.10, 3.2) is the plainer statement: gold and currency are not proper for monks, who neither accept nor receive them. Use it instead if the user prefers.

## Notes

- No branching, no resource list, no date box. The person writes it in their own words and the maintainer sorts it.
- Vinaya check (2026-10-22): the form never names, invites or gives examples of money, and the description says the maintainers do not deal with money, accept only time, energy, resources and pre-bought services, and do not accept donations. It names no specific needs, because hinting counts as asking. See the "Vinaya check" section of `spec.md`.
- Money, public thanks and country are not asked. Add them later only if offers show a need.
