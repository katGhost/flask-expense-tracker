export const darkMode = 'class';
export const content = [
  './templates/**/*.html',
  './static/**/*.js',
];
export const theme = {
  extend: {
    colors: {
      primary: {
        light: '#6D28D9',
        DEFAULT: '#5B21B6',
        dark: '#4C1D95',
      },
    }
  },
};
export const plugins = [
  tailwindcss/forms,
  tailwindcss/typography,
];
