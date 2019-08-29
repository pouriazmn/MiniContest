<template>
    <v-data-table dark
                  :headers="headers"
                  :items="teams"
                  :loading="loading"
                  class="elevation-1"
    >
    </v-data-table>
</template>

<script>
    export default {
        name: 'Scoreboard',
        data() {
            return {
                teams: [],
                loading: true,
                options: {},
                headers: [
                    {text: 'Rank', value: 'rank'},
                    {text: 'Name', value: 'name'},
                    {text: 'ID', value: 'id'},
                    {text: 'Score', value: 'score'},
                    {text: 'Problems', value: 'problems'},
                ],
            }
        },
        mounted() {
            let scoreboard_url = "/api/scoreboard/";
            this.$http.get(scoreboard_url).then(response => {
                this.teams = response.body
            });
            this.loading = false
        },
    }
</script>

