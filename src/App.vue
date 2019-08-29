<template>
    <v-app>
        <v-content>
            <v-container fluid>
                <Index/>
            </v-container>
        </v-content>
    </v-app>
</template>

<script>
    import Index from '@/views/Index';

    export default {
        name: 'App',
        components: {
            Index,
        },
        data: () => ({
            //
        }),
    };
</script>
