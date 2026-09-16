export const en = {
  app: {
    name: "Markowitz Playground",
    navigation: {
      optimize: "Optimize",
      learn: "Learn",
      about: "About",
    },
  },

  hero: {
    eyebrow: "PORTFOLIO OPTIMIZATION · EDUCATIONAL PLAYGROUND",
    title: "What does Markowitz make of these assets?",
    description:
      "Select real market instruments and explore how Modern Portfolio Theory combines them based on return, risk and correlation.",
  },

  samples: {
  title: "Sample assets for exploration",
  description:
    "The Markowitz model currently uses only this cached sample universe. Additional instruments can be identified by WKN and added to the list, but they are not included in the optimization until they are part of the sample cache.",
  },

  assets: {
    ineligibleBadge: "Identified · not in sample cache",
  },

  assetInput: {
  label: "Add an asset",
  placeholder: "Enter WKN",
  button: "Add asset",
  loading: "Looking up...",
  counter: "assets",
  maximum: 20,
  },

  emptyState: {
    title: "Start with your first asset",
    description:
      "Add at least two instruments to compare how they behave together.",
  },

  actions: {
    optimize: "Run Markowitz model",
  },

  errors: {
    INSTRUMENT_NOT_FOUND: {
      title: "Asset not found",
      message:
        "We could not identify an asset with this identifier.",
    },

    IDENTIFICATION_PROVIDER_UNAVAILABLE: {
      title: "Instrument lookup temporarily unavailable",
      message:
        "OpenFIGI could not be reached. Please try again later.",
    },

    INVALID_SAMPLE_SELECTION: {
      title: "Selection cannot be optimized",
      message:
        "The model currently runs only on the cached sample assets. Remove unidentified or non-sample instruments from the request, and keep at least two sample assets.",
    },

    OPTIMIZATION_FAILED: {
      title: "Optimization failed",
      message:
        "The model could not be run for this selection.",
    },

    INTERNAL_ERROR: {
      title: "Something went wrong",
      message:
        "The request could not be completed.",
    },
  },

  footer: {
    disclaimer:
      "For educational purposes only — not investment advice.",
  },
};