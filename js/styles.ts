import { css } from "lit";

export const materialStyles = css`
    @font-face {
        font-family: "Material Symbols Outlined";
        font-style: normal;
        font-weight: 400;
        src: url(https://fonts.gstatic.com/s/materialsymbolsoutlined/v205/kJF1BvYX7BgnkSrUwT8OhrdQw4oELdPIeeII9v6oDMzByHX9rA6RzaxHMPdY43zj-jCxv3fzvRNU22ZXGJpEpjC_1v-p_4MrImHCIJIZrDCvHOejbd5zrDAt.woff2)
            format("woff2");
    }

    .material-symbols-outlined {
        -webkit-font-feature-settings: "liga";
        -webkit-font-smoothing: antialiased;
        direction: ltr;
        display: inline-block;
        font-family: "Material Symbols Outlined";
        font-style: normal;
        font-weight: normal;
        letter-spacing: normal;
        line-height: 1;
        text-transform: none;
        white-space: nowrap;
        word-wrap: normal;
    }
`;
