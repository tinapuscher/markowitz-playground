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
    "This sample selection includes commonly used instruments representing markets and asset classes often found in investment portfolios. It is provided solely to explore how the Markowitz model works and does not represent a recommended portfolio or investment advice.",
  },

  assetInput: {
  label: "Add an asset",
  placeholder: "Enter WKN or ISIN",
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

    PRICE_DATA_UNAVAILABLE: {
      title: "Historical price data unavailable",
      message:
        "The asset was identified, but could not be reliably matched to historical price data from Yahoo Finance.",
    },

    MARKET_DATA_PROVIDER_UNAVAILABLE: {
      title: "Market data temporarily unavailable",
      message:
        "Yahoo Finance is currently limiting data requests. Please try again later.",
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